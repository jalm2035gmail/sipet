"""
Servicio de Machine Learning para el módulo de capacitación.

Este módulo contiene funcionalidades de ML/IA para:
- Recomendación de cursos personalizados
- Predicción de riesgo de abandono
- Análisis de sentimiento en encuestas
- Detección de patrones de aprendizaje
- Optimización de rutas de aprendizaje
- Clasificación automática de contenido
"""

from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from fastapi_modulo.modulos.capacitacion.repositorios import (
    cursos_repository,
    inscripciones_repository
)
from fastapi_modulo.modulos.capacitacion.servicios.utils import (
    calculate_percentage,
    normalize_string
)


# Configurar logger
logger = logging.getLogger(__name__)


# ============================================================================
# SISTEMA DE RECOMENDACIÓN DE CURSOS
# ============================================================================

class CursoRecommender:
    """
    Sistema de recomendación de cursos basado en múltiples estrategias.
    
    Combina:
    - Filtrado colaborativo
    - Filtrado basado en contenido
    - Filtrado basado en popularidad
    - Reglas de negocio
    """
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2)
        )
    
    def recomendar_cursos(
        self,
        colaborador_key: str,
        limit: int = 5,
        tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Recomienda cursos personalizados para un colaborador.
        
        Args:
            colaborador_key: Identificador del colaborador
            limit: Número máximo de recomendaciones
            tenant_id: ID del tenant
            
        Returns:
            Lista de cursos recomendados con score
        """
        try:
            logger.info(f"Generando recomendaciones para {colaborador_key}")
            
            db = inscripciones_repository.get_db()
            
            try:
                # Obtener historial del colaborador
                inscripciones = inscripciones_repository.list_inscripciones(
                    db=db,
                    colaborador_key=colaborador_key
                )
                
                # Obtener cursos disponibles
                cursos_disponibles = cursos_repository.list_cursos(
                    db=db,
                    estado="publicado"
                )
                
                # Filtrar cursos ya tomados
                cursos_tomados_ids = {
                    insc.curso_id for insc in inscripciones
                }
                
                cursos_candidatos = [
                    curso for curso in cursos_disponibles
                    if curso.id not in cursos_tomados_ids
                ]
                
                if not cursos_candidatos:
                    return []
                
                # Calcular scores combinando diferentes estrategias
                recomendaciones = []
                
                for curso in cursos_candidatos:
                    score = self._calcular_score_recomendacion(
                        db,
                        colaborador_key,
                        curso,
                        inscripciones
                    )
                    
                    recomendaciones.append({
                        "curso_id": curso.id,
                        "nombre": curso.nombre,
                        "descripcion": curso.descripcion,
                        "categoria_id": curso.categoria_id,
                        "nivel": curso.nivel,
                        "duracion_horas": curso.duracion_horas,
                        "score": score,
                        "razon": self._explicar_recomendacion(score)
                    })
                
                # Ordenar por score y limitar
                recomendaciones.sort(key=lambda x: x["score"], reverse=True)
                
                return recomendaciones[:limit]
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error al generar recomendaciones: {e}")
            return []
    
    def _calcular_score_recomendacion(
        self,
        db,
        colaborador_key: str,
        curso,
        inscripciones_colaborador
    ) -> float:
        """
        Calcula el score de recomendación combinando múltiples factores.
        
        Args:
            db: Sesión de base de datos
            colaborador_key: Identificador del colaborador
            curso: Objeto del curso
            inscripciones_colaborador: Inscripciones del colaborador
            
        Returns:
            Score de recomendación (0-100)
        """
        scores = []
        
        # 1. Score por similitud de contenido (30%)
        score_contenido = self._score_similitud_contenido(
            curso,
            inscripciones_colaborador
        )
        scores.append(score_contenido * 0.3)
        
        # 2. Score por popularidad (20%)
        score_popularidad = self._score_popularidad(db, curso)
        scores.append(score_popularidad * 0.2)
        
        # 3. Score por tendencia (15%)
        score_tendencia = self._score_tendencia(db, curso)
        scores.append(score_tendencia * 0.15)
        
        # 4. Score por filtrado colaborativo (25%)
        score_colaborativo = self._score_colaborativo(
            db,
            colaborador_key,
            curso
        )
        scores.append(score_colaborativo * 0.25)
        
        # 5. Score por nivel apropiado (10%)
        score_nivel = self._score_nivel_apropiado(
            curso,
            inscripciones_colaborador
        )
        scores.append(score_nivel * 0.1)
        
        return sum(scores)
    
    def _score_similitud_contenido(
        self,
        curso,
        inscripciones_colaborador
    ) -> float:
        """
        Calcula score basado en similitud de contenido.
        
        Args:
            curso: Curso a evaluar
            inscripciones_colaborador: Inscripciones del colaborador
            
        Returns:
            Score de similitud (0-100)
        """
        if not inscripciones_colaborador:
            return 50.0  # Neutral
        
        # Obtener cursos completados con buena calificación
        cursos_gustados = [
            insc.curso for insc in inscripciones_colaborador
            if insc.estado == "completado" and 
            (insc.puntaje_final or 0) >= 80
        ]
        
        if not cursos_gustados:
            return 50.0
        
        # Calcular similitud de texto
        try:
            textos_gustados = [
                f"{c.nombre} {c.descripcion or ''} {c.objetivo or ''}"
                for c in cursos_gustados
            ]
            
            texto_curso = f"{curso.nombre} {curso.descripcion or ''} {curso.objetivo or ''}"
            
            todos_textos = textos_gustados + [texto_curso]
            
            # Calcular TF-IDF
            tfidf_matrix = self.vectorizer.fit_transform(todos_textos)
            
            # Calcular similitud coseno
            similitud = cosine_similarity(
                tfidf_matrix[-1:],
                tfidf_matrix[:-1]
            )
            
            # Promedio de similitud
            score = float(np.mean(similitud) * 100)
            
            return min(100.0, max(0.0, score))
            
        except Exception as e:
            logger.warning(f"Error calculando similitud de contenido: {e}")
            return 50.0
    
    def _score_popularidad(self, db, curso) -> float:
        """
        Calcula score basado en popularidad del curso.
        
        Args:
            db: Sesión de base de datos
            curso: Curso a evaluar
            
        Returns:
            Score de popularidad (0-100)
        """
        try:
            # Contar inscripciones del curso
            total_inscripciones = inscripciones_repository.list_inscripciones_activas_por_curso(
                db,
                curso.id
            )
            
            num_inscripciones = len(total_inscripciones)
            
            # Normalizar a escala 0-100
            # Asumiendo que 100+ inscripciones es muy popular
            score = min(100.0, (num_inscripciones / 100) * 100)
            
            return score
            
        except Exception as e:
            logger.warning(f"Error calculando popularidad: {e}")
            return 50.0
    
    def _score_tendencia(self, db, curso) -> float:
        """
        Calcula score basado en tendencia reciente.
        
        Args:
            db: Sesión de base de datos
            curso: Curso a evaluar
            
        Returns:
            Score de tendencia (0-100)
        """
        try:
            # Obtener inscripciones del último mes
            hace_un_mes = (datetime.utcnow() - timedelta(days=30)).isoformat()
            
            inscripciones_recientes = inscripciones_repository.list_inscripciones(
                db,
                curso_id=curso.id,
                fecha_desde=hace_un_mes
            )
            
            # Normalizar
            num_recientes = len(inscripciones_recientes)
            score = min(100.0, (num_recientes / 50) * 100)
            
            return score
            
        except Exception as e:
            logger.warning(f"Error calculando tendencia: {e}")
            return 50.0
    
    def _score_colaborativo(
        self,
        db,
        colaborador_key: str,
        curso
    ) -> float:
        """
        Calcula score usando filtrado colaborativo.
        
        "Usuarios similares a ti también tomaron este curso"
        
        Args:
            db: Sesión de base de datos
            colaborador_key: Identificador del colaborador
            curso: Curso a evaluar
            
        Returns:
            Score colaborativo (0-100)
        """
        try:
            # Obtener inscripciones del colaborador
            mis_inscripciones = inscripciones_repository.list_inscripciones(
                db,
                colaborador_key=colaborador_key
            )
            
            mis_cursos_ids = {insc.curso_id for insc in mis_inscripciones}
            
            if not mis_cursos_ids:
                return 50.0
            
            # Encontrar colaboradores con cursos en común
            colaboradores_similares = set()
            
            for curso_id in mis_cursos_ids:
                inscripciones_curso = inscripciones_repository.list_inscripciones(
                    db,
                    curso_id=curso_id
                )
                
                for insc in inscripciones_curso:
                    if insc.colaborador_key != colaborador_key:
                        colaboradores_similares.add(insc.colaborador_key)
            
            if not colaboradores_similares:
                return 50.0
            
            # Contar cuántos tomaron el curso recomendado
            toman_curso = 0
            
            for colab_key in colaboradores_similares:
                inscripciones_colab = inscripciones_repository.list_inscripciones(
                    db,
                    colaborador_key=colab_key,
                    curso_id=curso.id
                )
                
                if inscripciones_colab:
                    toman_curso += 1
            
            # Calcular score
            score = (toman_curso / len(colaboradores_similares)) * 100
            
            return score
            
        except Exception as e:
            logger.warning(f"Error en filtrado colaborativo: {e}")
            return 50.0
    
    def _score_nivel_apropiado(self, curso, inscripciones_colaborador) -> float:
        """
        Calcula score basado en si el nivel es apropiado.
        
        Args:
            curso: Curso a evaluar
            inscripciones_colaborador: Inscripciones del colaborador
            
        Returns:
            Score de nivel apropiado (0-100)
        """
        if not inscripciones_colaborador:
            # Sin historial, cursos básicos son mejores
            niveles_score = {
                "basico": 100,
                "intermedio": 70,
                "avanzado": 40
            }
            return niveles_score.get(curso.nivel or "basico", 50)
        
        # Analizar nivel de cursos completados
        niveles_completados = [
            insc.curso.nivel for insc in inscripciones_colaborador
            if insc.estado == "completado" and insc.curso
        ]
        
        nivel_map = {"basico": 1, "intermedio": 2, "avanzado": 3}
        
        if niveles_completados:
            nivel_promedio = np.mean([
                nivel_map.get(n, 1) for n in niveles_completados
            ])
            
            nivel_curso = nivel_map.get(curso.nivel or "basico", 1)
            
            # Preferir nivel similar o un poco más alto
            diff = abs(nivel_curso - nivel_promedio)
            
            if diff == 0:
                return 100.0
            elif diff == 1:
                return 80.0 if nivel_curso > nivel_promedio else 70.0
            else:
                return 50.0
        
        return 50.0
    
    def _explicar_recomendacion(self, score: float) -> str:
        """
        Genera una explicación textual de la recomendación.
        
        Args:
            score: Score de recomendación
            
        Returns:
            Texto explicativo
        """
        if score >= 80:
            return "Altamente recomendado basado en tu perfil"
        elif score >= 60:
            return "Recomendado para ti"
        elif score >= 40:
            return "Podría interesarte"
        else:
            return "Relacionado con tus intereses"


# ============================================================================
# PREDICCIÓN DE RIESGO DE ABANDONO
# ============================================================================

class RiesgoAbandonoPredictor:
    """
    Predictor de riesgo de abandono de cursos.
    
    Analiza patrones de comportamiento para identificar colaboradores
    en riesgo de abandonar un curso.
    """
    
    def predecir_riesgo(
        self,
        inscripcion_id: int,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Predice el riesgo de abandono para una inscripción.
        
        Args:
            inscripcion_id: ID de la inscripción
            tenant_id: ID del tenant
            
        Returns:
            Diccionario con predicción y factores de riesgo
        """
        try:
            db = inscripciones_repository.get_db()
            
            try:
                inscripcion = inscripciones_repository.get_inscripcion(
                    db,
                    inscripcion_id
                )
                
                if not inscripcion:
                    return {
                        "riesgo": "desconocido",
                        "score": 0,
                        "factores": []
                    }
                
                # Calcular factores de riesgo
                factores = []
                score_total = 0
                
                # Factor 1: Tiempo sin actividad
                score_inactividad, desc_inactividad = self._factor_inactividad(
                    inscripcion
                )
                if score_inactividad > 0:
                    factores.append({
                        "factor": "inactividad",
                        "score": score_inactividad,
                        "descripcion": desc_inactividad
                    })
                    score_total += score_inactividad
                
                # Factor 2: Bajo porcentaje de avance
                score_avance, desc_avance = self._factor_bajo_avance(inscripcion)
                if score_avance > 0:
                    factores.append({
                        "factor": "bajo_avance",
                        "score": score_avance,
                        "descripcion": desc_avance
                    })
                    score_total += score_avance
                
                # Factor 3: Intentos fallidos en evaluaciones
                score_intentos, desc_intentos = self._factor_intentos_fallidos(
                    db,
                    inscripcion
                )
                if score_intentos > 0:
                    factores.append({
                        "factor": "intentos_fallidos",
                        "score": score_intentos,
                        "descripcion": desc_intentos
                    })
                    score_total += score_intentos
                
                # Factor 4: Proximidad a vencimiento
                score_vencimiento, desc_vencimiento = self._factor_vencimiento(
                    inscripcion
                )
                if score_vencimiento > 0:
                    factores.append({
                        "factor": "proximo_vencimiento",
                        "score": score_vencimiento,
                        "descripcion": desc_vencimiento
                    })
                    score_total += score_vencimiento
                
                # Determinar nivel de riesgo
                if score_total >= 70:
                    riesgo = "alto"
                elif score_total >= 40:
                    riesgo = "medio"
                elif score_total >= 20:
                    riesgo = "bajo"
                else:
                    riesgo = "muy_bajo"
                
                return {
                    "inscripcion_id": inscripcion_id,
                    "riesgo": riesgo,
                    "score": score_total,
                    "factores": factores,
                    "recomendaciones": self._generar_recomendaciones(factores)
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error al predecir riesgo de abandono: {e}")
            return {
                "riesgo": "error",
                "score": 0,
                "factores": [],
                "error": str(e)
            }
    
    def _factor_inactividad(self, inscripcion) -> Tuple[float, str]:
        """
        Calcula factor de riesgo por inactividad.
        
        Args:
            inscripcion: Objeto de inscripción
            
        Returns:
            Tupla (score, descripción)
        """
        if not inscripcion.fecha_inicio_real:
            return 0, ""
        
        dias_inactivo = (datetime.utcnow() - inscripcion.fecha_inicio_real).days
        
        if dias_inactivo >= 14:
            return 30, f"{dias_inactivo} días sin actividad"
        elif dias_inactivo >= 7:
            return 15, f"{dias_inactivo} días sin actividad"
        
        return 0, ""
    
    def _factor_bajo_avance(self, inscripcion) -> Tuple[float, str]:
        """
        Calcula factor de riesgo por bajo avance.
        
        Args:
            inscripcion: Objeto de inscripción
            
        Returns:
            Tupla (score, descripción)
        """
        avance = inscripcion.pct_avance or 0
        
        if not inscripcion.fecha_inicio_real:
            return 0, ""
        
        dias_cursando = (datetime.utcnow() - inscripcion.fecha_inicio_real).days
        
        # Si lleva más de una semana y tiene menos de 20% de avance
        if dias_cursando >= 7 and avance < 20:
            return 25, f"Solo {avance}% de avance en {dias_cursando} días"
        elif dias_cursando >= 14 and avance < 50:
            return 20, f"Solo {avance}% de avance en {dias_cursando} días"
        
        return 0, ""
    
    def _factor_intentos_fallidos(self, db, inscripcion) -> Tuple[float, str]:
        """
        Calcula factor de riesgo por intentos fallidos en evaluaciones.
        
        Args:
            db: Sesión de base de datos
            inscripcion: Objeto de inscripción
            
        Returns:
            Tupla (score, descripción)
        """
        try:
            # Obtener intentos de evaluación
            intentos = evaluaciones_repository.list_intentos(
                db,
                inscripcion.id
            )
            
            if not intentos:
                return 0, ""
            
            intentos_fallidos = [
                intento for intento in intentos
                if not intento.aprobado
            ]
            
            if len(intentos_fallidos) >= 3:
                return 25, f"{len(intentos_fallidos)} intentos fallidos en evaluaciones"
            elif len(intentos_fallidos) >= 2:
                return 15, f"{len(intentos_fallidos)} intentos fallidos en evaluaciones"
            
            return 0, ""
            
        except Exception:
            return 0, ""
    
    def _factor_vencimiento(self, inscripcion) -> Tuple[float, str]:
        """
        Calcula factor de riesgo por proximidad a vencimiento.
        
        Args:
            inscripcion: Objeto de inscripción
            
        Returns:
            Tupla (score, descripción)
        """
        if not inscripcion.fecha_vencimiento:
            return 0, ""
        
        dias_restantes = (inscripcion.fecha_vencimiento - datetime.utcnow()).days
        avance = inscripcion.pct_avance or 0
        
        # Si está próximo a vencer y tiene bajo avance
        if dias_restantes <= 7 and avance < 70:
            return 30, f"Vence en {dias_restantes} días con {avance}% de avance"
        elif dias_restantes <= 14 and avance < 50:
            return 20, f"Vence en {dias_restantes} días con {avance}% de avance"
        
        return 0, ""
    
    def _generar_recomendaciones(self, factores: List[Dict]) -> List[str]:
        """
        Genera recomendaciones basadas en factores de riesgo.
        
        Args:
            factores: Lista de factores de riesgo
            
        Returns:
            Lista de recomendaciones
        """
        recomendaciones = []
        
        for factor in factores:
            if factor["factor"] == "inactividad":
                recomendaciones.append(
                    "Enviar recordatorio personalizado para retomar el curso"
                )
            elif factor["factor"] == "bajo_avance":
                recomendaciones.append(
                    "Ofrecer sesión de tutoría o soporte adicional"
                )
            elif factor["factor"] == "intentos_fallidos":
                recomendaciones.append(
                    "Proporcionar material de repaso o recursos adicionales"
                )
            elif factor["factor"] == "proximo_vencimiento":
                recomendaciones.append(
                    "Considerar extensión de plazo o plan de recuperación"
                )
        
        return recomendaciones


# ============================================================================
# ANÁLISIS DE SENTIMIENTO EN ENCUESTAS
# ============================================================================

class SentimientoAnalyzer:
    """
    Analizador de sentimiento para comentarios de encuestas de satisfacción.
    
    Clasifica comentarios como positivos, negativos o neutrales.
    """
    
    # Palabras clave por sentimiento
    PALABRAS_POSITIVAS = {
        'excelente', 'bueno', 'genial', 'útil', 'claro', 'interesante',
        'práctico', 'completo', 'recomendable', 'informativo', 'didáctico',
        'ameno', 'profesional', 'valioso', 'efectivo', 'motivador'
    }
    
    PALABRAS_NEGATIVAS = {
        'malo', 'aburrido', 'confuso', 'difícil', 'largo', 'complicado',
        'tedioso', 'innecesario', 'perdida', 'tiempo', 'desorganizado',
        'obsoleto', 'incompleto', 'frustrante', 'deficiente'
    }
    
    def analizar_comentario(self, comentario: str) -> Dict[str, Any]:
        """
        Analiza el sentimiento de un comentario.
        
        Args:
            comentario: Texto del comentario
            
        Returns:
            Diccionario con análisis de sentimiento
        """
        if not comentario:
            return {
                "sentimiento": "neutral",
                "score": 0,
                "confianza": 0
            }
        
        # Normalizar texto
        texto = normalize_string(comentario)
        palabras = set(texto.split())
        
        # Contar palabras positivas y negativas
        positivas = len(palabras & self.PALABRAS_POSITIVAS)
        negativas = len(palabras & self.PALABRAS_NEGATIVAS)
        
        # Calcular score (-1 a 1)
        total = positivas + negativas
        
        if total == 0:
            return {
                "sentimiento": "neutral",
                "score": 0,
                "confianza": 0.3
            }
        
        score = (positivas - negativas) / total
        confianza = min(total / 5, 1.0)  # Máximo 5 palabras clave
        
        # Determinar sentimiento
        if score > 0.2:
            sentimiento = "positivo"
        elif score < -0.2:
            sentimiento = "negativo"
        else:
            sentimiento = "neutral"
        
        return {
            "sentimiento": sentimiento,
            "score": score,
            "confianza": confianza,
            "palabras_clave": {
                "positivas": positivas,
                "negativas": negativas
            }
        }
    
    def analizar_lote(
        self,
        comentarios: List[str]
    ) -> Dict[str, Any]:
        """
        Analiza múltiples comentarios y genera estadísticas.
        
        Args:
            comentarios: Lista de comentarios
            
        Returns:
            Diccionario con análisis agregado
        """
        if not comentarios:
            return {
                "total": 0,
                "positivos": 0,
                "negativos": 0,
                "neutrales": 0,
                "score_promedio": 0
            }
        
        resultados = [
            self.analizar_comentario(c) for c in comentarios
        ]
        
        sentimientos = Counter([r["sentimiento"] for r in resultados])
        scores = [r["score"] for r in resultados]
        
        return {
            "total": len(comentarios),
            "positivos": sentimientos.get("positivo", 0),
            "negativos": sentimientos.get("negativo", 0),
            "neutrales": sentimientos.get("neutral", 0),
            "score_promedio": np.mean(scores) if scores else 0,
            "distribucion_porcentual": {
                "positivos": calculate_percentage(
                    sentimientos.get("positivo", 0),
                    len(comentarios)
                ),
                "negativos": calculate_percentage(
                    sentimientos.get("negativo", 0),
                    len(comentarios)
                ),
                "neutrales": calculate_percentage(
                    sentimientos.get("neutral", 0),
                    len(comentarios)
                )
            }
        }


# ============================================================================
# DETECCIÓN DE PATRONES DE APRENDIZAJE
# ============================================================================

class PatronesAprendizajeDetector:
    """
    Detector de patrones de aprendizaje de colaboradores.
    
    Identifica:
    - Horarios preferidos de estudio
    - Velocidad de aprendizaje
    - Estilo de aprendizaje
    - Días de mayor actividad
    """
    
    def detectar_patrones(
        self,
        colaborador_key: str,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detecta patrones de aprendizaje de un colaborador.
        
        Args:
            colaborador_key: Identificador del colaborador
            tenant_id: ID del tenant
            
        Returns:
            Diccionario con patrones detectados
        """
        try:
            db = inscripciones_repository.get_db()
            
            try:
                # Obtener historial del colaborador
                inscripciones = inscripciones_repository.list_inscripciones(
                    db,
                    colaborador_key=colaborador_key
                )
                
                if not inscripciones:
                    return {
                        "patrones_detectados": False,
                        "mensaje": "Datos insuficientes"
                    }
                
                patrones = {
                    "velocidad_aprendizaje": self._analizar_velocidad(
                        inscripciones
                    ),
                    "consistencia": self._analizar_consistencia(inscripciones),
                    "nivel_compromiso": self._analizar_compromiso(inscripciones),
                    "preferencias": self._analizar_preferencias(inscripciones)
                }
                
                return {
                    "patrones_detectados": True,
                    "colaborador_key": colaborador_key,
                    **patrones
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error al detectar patrones: {e}")
            return {
                "patrones_detectados": False,
                "error": str(e)
            }
    
    def _analizar_velocidad(self, inscripciones) -> Dict[str, Any]:
        """
        Analiza velocidad de aprendizaje.
        
        Args:
            inscripciones: Lista de inscripciones
            
        Returns:
            Análisis de velocidad
        """
        completadas = [
            i for i in inscripciones
            if i.estado == "completado" and 
            i.fecha_inscripcion and 
            i.fecha_completado
        ]
        
        if not completadas:
            return {"categoria": "desconocida", "dias_promedio": 0}
        
        dias_completar = [
            (i.fecha_completado - i.fecha_inscripcion).days
            for i in completadas
        ]
        
        promedio = np.mean(dias_completar)
        
        if promedio <= 7:
            categoria = "rapida"
        elif promedio <= 30:
            categoria = "moderada"
        else:
            categoria = "pausada"
        
        return {
            "categoria": categoria,
            "dias_promedio": round(promedio, 1)
        }
    
    def _analizar_consistencia(self, inscripciones) -> Dict[str, Any]:
        """
        Analiza consistencia en completar cursos.
        
        Args:
            inscripciones: Lista de inscripciones
            
        Returns:
            Análisis de consistencia
        """
        if not inscripciones:
            return {"nivel": "desconocido", "tasa_completado": 0}
        
        completadas = sum(
            1 for i in inscripciones
            if i.estado == "completado"
        )
        
        tasa = calculate_percentage(completadas, len(inscripciones))
        
        if tasa >= 80:
            nivel = "alta"
        elif tasa >= 50:
            nivel = "media"
        else:
            nivel = "baja"
        
        return {
            "nivel": nivel,
            "tasa_completado": tasa,
            "total_inscritos": len(inscripciones),
            "total_completados": completadas
        }
    
    def _analizar_compromiso(self, inscripciones) -> Dict[str, Any]:
        """
        Analiza nivel de compromiso.
        
        Args:
            inscripciones: Lista de inscripciones
            
        Returns:
            Análisis de compromiso
        """
        if not inscripciones:
            return {"nivel": "desconocido"}
        
        # Factores de compromiso
        puntajes_altos = sum(
            1 for i in inscripciones
            if (i.puntaje_final or 0) >= 90
        )
        
        avance_alto = sum(
            1 for i in inscripciones
            if (i.pct_avance or 0) >= 70
        )
        
        # Calcular nivel
        score = (puntajes_altos + avance_alto) / (len(inscripciones) * 2)
        
        if score >= 0.7:
            nivel = "alto"
        elif score >= 0.4:
            nivel = "medio"
        else:
            nivel = "bajo"
        
        return {
            "nivel": nivel,
            "score": round(score * 100, 1)
        }
    
    def _analizar_preferencias(self, inscripciones) -> Dict[str, Any]:
        """
        Analiza preferencias de aprendizaje.
        
        Args:
            inscripciones: Lista de inscripciones
            
        Returns:
            Análisis de preferencias
        """
        # Categorías más frecuentes
        categorias = [
            i.curso.categoria.nombre
            for i in inscripciones
            if i.curso and i.curso.categoria
        ]
        
        categoria_preferida = None
        if categorias:
            contador = Counter(categorias)
            categoria_preferida = contador.most_common(1)[0][0]
        
        # Niveles más frecuentes
        niveles = [
            i.curso.nivel
            for i in inscripciones
            if i.curso and i.curso.nivel
        ]
        
        nivel_preferido = None
        if niveles:
            contador = Counter(niveles)
            nivel_preferido = contador.most_common(1)[0][0]
        
        return {
            "categoria_preferida": categoria_preferida,
            "nivel_preferido": nivel_preferido,
            "total_categorias": len(set(categorias)) if categorias else 0
        }


# ============================================================================
# INSTANCIAS GLOBALES
# ============================================================================

# Instancias singleton para reutilización
curso_recommender = CursoRecommender()
riesgo_predictor = RiesgoAbandonoPredictor()
sentimiento_analyzer = SentimientoAnalyzer()
patrones_detector = PatronesAprendizajeDetector()


# ============================================================================
# FUNCIONES DE CONVENIENCIA
# ============================================================================

def recomendar_cursos(
    colaborador_key: str,
    limit: int = 5,
    tenant_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Función de conveniencia para recomendación de cursos.
    
    Args:
        colaborador_key: Identificador del colaborador
        limit: Número máximo de recomendaciones
        tenant_id: ID del tenant
        
    Returns:
        Lista de cursos recomendados
    """
    return curso_recommender.recomendar_cursos(
        colaborador_key,
        limit,
        tenant_id
    )


def predecir_riesgo_abandono(
    inscripcion_id: int,
    tenant_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Función de conveniencia para predicción de riesgo.
    
    Args:
        inscripcion_id: ID de la inscripción
        tenant_id: ID del tenant
        
    Returns:
        Predicción de riesgo
    """
    return riesgo_predictor.predecir_riesgo(inscripcion_id, tenant_id)


def analizar_sentimiento(comentario: str) -> Dict[str, Any]:
    """
    Función de conveniencia para análisis de sentimiento.
    
    Args:
        comentario: Texto del comentario
        
    Returns:
        Análisis de sentimiento
    """
    return sentimiento_analyzer.analizar_comentario(comentario)


def detectar_patrones_aprendizaje(
    colaborador_key: str,
    tenant_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Función de conveniencia para detección de patrones.
    
    Args:
        colaborador_key: Identificador del colaborador
        tenant_id: ID del tenant
        
    Returns:
        Patrones de aprendizaje detectados
    """
    return patrones_detector.detectar_patrones(colaborador_key, tenant_id)
