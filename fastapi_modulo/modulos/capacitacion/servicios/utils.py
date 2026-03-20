"""
Módulo de utilidades para el módulo de capacitación.

Contiene funciones auxiliares reutilizables para:
- Serialización y deserialización de JSON
- Formateo de fechas y tiempos
- Validaciones comunes
- Generación de códigos únicos
- Helpers de paginación
- Funciones de transformación de datos
"""

from __future__ import annotations

import json
import random
import re
import string
import uuid
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy import func
from sqlalchemy.orm import Query, Session


# ============================================================================
# SERIALIZACIÓN Y DESERIALIZACIÓN
# ============================================================================

def safe_json_loads(
    value: Any,
    fallback: Any = None,
    raise_on_error: bool = False
) -> Any:
    """
    Deserializa un JSON string de forma segura.
    
    Args:
        value: String JSON, dict, list o None
        fallback: Valor de respaldo si falla la deserialización
        raise_on_error: Si debe lanzar excepción en caso de error
        
    Returns:
        Objeto deserializado o fallback
        
    Raises:
        ValueError: Si raise_on_error=True y falla la deserialización
    
    Examples:
        >>> safe_json_loads('{"key": "value"}')
        {'key': 'value'}
        >>> safe_json_loads('invalid', fallback={})
        {}
        >>> safe_json_loads(None, fallback=[])
        []
    """
    if value is None:
        return fallback
    
    if isinstance(value, (dict, list)):
        return value
    
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError) as e:
        if raise_on_error:
            raise ValueError(f"Error al deserializar JSON: {e}")
        return fallback


def safe_json_dumps(
    value: Any,
    pretty: bool = False,
    ensure_ascii: bool = False
) -> Optional[str]:
    """
    Serializa un objeto a JSON string de forma segura.
    
    Args:
        value: Objeto a serializar
        pretty: Si debe formatear con indentación
        ensure_ascii: Si debe escapar caracteres no-ASCII
        
    Returns:
        String JSON o None si value es None
    
    Examples:
        >>> safe_json_dumps({'key': 'value'})
        '{"key": "value"}'
        >>> safe_json_dumps(None)
        None
        >>> safe_json_dumps({'a': 1}, pretty=True)
        '{\\n  "a": 1\\n}'
    """
    if value is None:
        return None
    
    if isinstance(value, str):
        return value
    
    kwargs = {"ensure_ascii": ensure_ascii}
    if pretty:
        kwargs.update({"indent": 2, "sort_keys": True})
    
    return json.dumps(value, **kwargs)


# ============================================================================
# FORMATEO DE FECHAS Y TIEMPOS
# ============================================================================

def datetime_to_iso(value: Optional[datetime]) -> Optional[str]:
    """
    Convierte un datetime a formato ISO 8601 string.
    
    Args:
        value: Objeto datetime o None
        
    Returns:
        String ISO 8601 o None
    
    Examples:
        >>> datetime_to_iso(datetime(2024, 1, 15, 10, 30))
        '2024-01-15T10:30:00'
        >>> datetime_to_iso(None)
        None
    """
    if value is None:
        return None
    
    if isinstance(value, datetime):
        return value.isoformat()
    
    return str(value)


def date_to_string(value: Optional[date]) -> Optional[str]:
    """
    Convierte una fecha a string formato YYYY-MM-DD.
    
    Args:
        value: Objeto date o None
        
    Returns:
        String de fecha o None
    
    Examples:
        >>> date_to_string(date(2024, 1, 15))
        '2024-01-15'
        >>> date_to_string(None)
        None
    """
    if value is None:
        return None
    
    if isinstance(value, date):
        return value.isoformat()
    
    return str(value)


def string_to_datetime(
    value: Optional[str],
    default: Optional[datetime] = None
) -> Optional[datetime]:
    """
    Convierte un string a datetime de forma segura.
    
    Args:
        value: String con fecha/hora en formato ISO
        default: Valor por defecto si falla la conversión
        
    Returns:
        Objeto datetime o default
    
    Examples:
        >>> string_to_datetime('2024-01-15T10:30:00')
        datetime(2024, 1, 15, 10, 30)
        >>> string_to_datetime('invalid', default=None)
        None
    """
    if not value:
        return default
    
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return default


def string_to_date(
    value: Optional[str],
    default: Optional[date] = None
) -> Optional[date]:
    """
    Convierte un string a date de forma segura.
    
    Args:
        value: String con fecha en formato ISO (YYYY-MM-DD)
        default: Valor por defecto si falla la conversión
        
    Returns:
        Objeto date o default
    
    Examples:
        >>> string_to_date('2024-01-15')
        date(2024, 1, 15)
        >>> string_to_date('invalid', default=None)
        None
    """
    if not value:
        return default
    
    try:
        return date.fromisoformat(value)
    except (ValueError, AttributeError):
        return default


def format_duration(seconds: int) -> str:
    """
    Formatea una duración en segundos a formato legible.
    
    Args:
        seconds: Duración en segundos
        
    Returns:
        String formateado (ej: "2h 30m", "45m", "30s")
    
    Examples:
        >>> format_duration(9000)
        '2h 30m'
        >>> format_duration(120)
        '2m'
        >>> format_duration(45)
        '45s'
    """
    if seconds < 60:
        return f"{seconds}s"
    
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if remaining_minutes > 0:
        return f"{hours}h {remaining_minutes}m"
    
    return f"{hours}h"


def add_business_days(
    start_date: date,
    days: int,
    holidays: Optional[List[date]] = None
) -> date:
    """
    Añade días hábiles a una fecha, excluyendo fines de semana y festivos.
    
    Args:
        start_date: Fecha inicial
        days: Número de días hábiles a añadir
        holidays: Lista de fechas festivas a excluir
        
    Returns:
        Fecha resultante
    
    Examples:
        >>> add_business_days(date(2024, 1, 15), 5)
        date(2024, 1, 22)
    """
    holidays = holidays or []
    current_date = start_date
    days_added = 0
    
    while days_added < days:
        current_date += timedelta(days=1)
        
        # Saltar fines de semana (5=sábado, 6=domingo)
        if current_date.weekday() >= 5:
            continue
        
        # Saltar festivos
        if current_date in holidays:
            continue
        
        days_added += 1
    
    return current_date


# ============================================================================
# GENERACIÓN DE CÓDIGOS Y TOKENS
# ============================================================================

def generate_code(
    prefix: str = "",
    length: int = 8,
    uppercase: bool = True,
    include_digits: bool = True
) -> str:
    """
    Genera un código alfanumérico aleatorio.
    
    Args:
        prefix: Prefijo opcional para el código
        length: Longitud de la parte aleatoria
        uppercase: Si debe usar mayúsculas
        include_digits: Si debe incluir dígitos
        
    Returns:
        Código generado
    
    Examples:
        >>> generate_code(prefix="CAP", length=6)
        'CAP-A1B2C3'
        >>> generate_code(length=8, uppercase=False)
        'ab12cd34'
    """
    chars = string.ascii_uppercase if uppercase else string.ascii_lowercase
    
    if include_digits:
        chars += string.digits
    
    random_part = ''.join(random.choices(chars, k=length))
    
    if prefix:
        return f"{prefix}-{random_part}"
    
    return random_part


def generate_uuid() -> str:
    """
    Genera un UUID versión 4.
    
    Returns:
        String UUID
    
    Examples:
        >>> uuid_str = generate_uuid()
        >>> len(uuid_str)
        36
    """
    return str(uuid.uuid4())


def generate_short_uuid(length: int = 12) -> str:
    """
    Genera un UUID corto en hexadecimal.
    
    Args:
        length: Longitud del UUID corto
        
    Returns:
        String UUID corto en mayúsculas
    
    Examples:
        >>> short_uuid = generate_short_uuid(12)
        >>> len(short_uuid)
        12
    """
    return uuid.uuid4().hex[:length].upper()


def generate_folio(prefix: str = "CERT") -> str:
    """
    Genera un folio único para certificados u otros documentos.
    
    Args:
        prefix: Prefijo del folio
        
    Returns:
        Folio único
    
    Examples:
        >>> folio = generate_folio("CERT")
        >>> folio.startswith("CERT-")
        True
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    random_part = generate_short_uuid(6)
    
    return f"{prefix}-{timestamp}-{random_part}"


# ============================================================================
# VALIDACIONES
# ============================================================================

def is_valid_email(email: str) -> bool:
    """
    Valida si un string es un email válido.
    
    Args:
        email: String a validar
        
    Returns:
        True si es un email válido
    
    Examples:
        >>> is_valid_email('user@example.com')
        True
        >>> is_valid_email('invalid-email')
        False
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_url(url: str) -> bool:
    """
    Valida si un string es una URL válida.
    
    Args:
        url: String a validar
        
    Returns:
        True si es una URL válida
    
    Examples:
        >>> is_valid_url('https://example.com')
        True
        >>> is_valid_url('not-a-url')
        False
    """
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))


def validate_percentage(value: Union[int, float]) -> float:
    """
    Valida y normaliza un valor de porcentaje.
    
    Args:
        value: Valor a validar (0-100)
        
    Returns:
        Valor normalizado entre 0 y 100
    
    Raises:
        ValueError: Si el valor está fuera de rango
    
    Examples:
        >>> validate_percentage(75.5)
        75.5
        >>> validate_percentage(150)
        Traceback (most recent call last):
        ...
        ValueError: El porcentaje debe estar entre 0 y 100
    """
    value = float(value)
    
    if value < 0 or value > 100:
        raise ValueError("El porcentaje debe estar entre 0 y 100")
    
    return round(value, 2)


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitiza un nombre de archivo eliminando caracteres no válidos.
    
    Args:
        filename: Nombre de archivo original
        max_length: Longitud máxima permitida
        
    Returns:
        Nombre de archivo sanitizado
    
    Examples:
        >>> sanitize_filename('my file (1).pdf')
        'my_file_1.pdf'
        >>> sanitize_filename('archivo/invalido\\test.txt')
        'archivo_invalido_test.txt'
    """
    # Reemplazar caracteres no válidos
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Reemplazar espacios y paréntesis
    filename = re.sub(r'[\s()]', '_', filename)
    
    # Eliminar guiones bajos múltiples
    filename = re.sub(r'_+', '_', filename)
    
    # Truncar si es necesario
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_length = max_length - len(ext) - 1
        filename = f"{name[:max_name_length]}.{ext}" if ext else name[:max_length]
    
    return filename.strip('_')


# ============================================================================
# PAGINACIÓN
# ============================================================================

def paginate(
    query: Query,
    page: int = 1,
    per_page: int = 20,
    max_per_page: int = 100
) -> Dict[str, Any]:
    """
    Pagina una consulta SQLAlchemy.
    
    Args:
        query: Query de SQLAlchemy
        page: Número de página (base 1)
        per_page: Elementos por página
        max_per_page: Máximo de elementos por página
        
    Returns:
        Diccionario con datos de paginación
    
    Examples:
        >>> from sqlalchemy.orm import Query
        >>> # query = db.query(Model)
        >>> # result = paginate(query, page=2, per_page=10)
        >>> # result['items'], result['total'], result['pages']
    """
    # Validar parámetros
    page = max(1, int(page))
    per_page = min(max(1, int(per_page)), max_per_page)
    
    # Obtener total
    total = query.count()
    
    # Calcular offset
    offset = (page - 1) * per_page
    
    # Obtener items
    items = query.limit(per_page).offset(offset).all()
    
    # Calcular páginas totales
    pages = (total + per_page - 1) // per_page
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
        "has_prev": page > 1,
        "has_next": page < pages,
        "prev_page": page - 1 if page > 1 else None,
        "next_page": page + 1 if page < pages else None,
    }


def calculate_offset_limit(
    page: int = 1,
    per_page: int = 20
) -> Tuple[int, int]:
    """
    Calcula offset y limit para paginación manual.
    
    Args:
        page: Número de página (base 1)
        per_page: Elementos por página
        
    Returns:
        Tupla (offset, limit)
    
    Examples:
        >>> calculate_offset_limit(1, 20)
        (0, 20)
        >>> calculate_offset_limit(3, 10)
        (20, 10)
    """
    page = max(1, int(page))
    per_page = max(1, int(per_page))
    offset = (page - 1) * per_page
    
    return offset, per_page


# ============================================================================
# TRANSFORMACIÓN DE DATOS
# ============================================================================

def normalize_string(text: Optional[str], lowercase: bool = True) -> str:
    """
    Normaliza un string eliminando espacios extras y opcionalmente a minúsculas.
    
    Args:
        text: Texto a normalizar
        lowercase: Si debe convertir a minúsculas
        
    Returns:
        String normalizado
    
    Examples:
        >>> normalize_string('  Hello   World  ')
        'hello world'
        >>> normalize_string('  Test  ', lowercase=False)
        'Test'
    """
    if not text:
        return ""
    
    # Eliminar espacios extras
    text = ' '.join(text.split())
    
    if lowercase:
        text = text.lower()
    
    return text.strip()


def truncate_text(
    text: str,
    max_length: int = 100,
    suffix: str = "..."
) -> str:
    """
    Trunca un texto a una longitud máxima.
    
    Args:
        text: Texto a truncar
        max_length: Longitud máxima
        suffix: Sufijo a añadir si se trunca
        
    Returns:
        Texto truncado
    
    Examples:
        >>> truncate_text('This is a long text', 10)
        'This is...'
        >>> truncate_text('Short', 10)
        'Short'
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def slugify(text: str, max_length: int = 50) -> str:
    """
    Convierte un texto a formato slug (URL-friendly).
    
    Args:
        text: Texto a convertir
        max_length: Longitud máxima del slug
        
    Returns:
        Texto en formato slug
    
    Examples:
        >>> slugify('Hello World!')
        'hello-world'
        >>> slugify('Ñoño & Tilde')
        'nono-tilde'
    """
    # Convertir a minúsculas
    text = text.lower()
    
    # Reemplazar caracteres especiales
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', 'ü': 'u', 'à': 'a', 'è': 'e', 'ì': 'i',
        'ò': 'o', 'ù': 'u'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Eliminar caracteres no alfanuméricos
    text = re.sub(r'[^a-z0-9]+', '-', text)
    
    # Eliminar guiones al inicio y final
    text = text.strip('-')
    
    # Truncar si es necesario
    if len(text) > max_length:
        text = text[:max_length].rstrip('-')
    
    return text


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combina múltiples diccionarios en uno solo.
    
    Args:
        *dicts: Diccionarios a combinar
        
    Returns:
        Diccionario combinado (los últimos sobrescriben a los primeros)
    
    Examples:
        >>> merge_dicts({'a': 1}, {'b': 2}, {'a': 3})
        {'a': 3, 'b': 2}
    """
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def flatten_dict(
    data: Dict[str, Any],
    parent_key: str = '',
    sep: str = '.'
) -> Dict[str, Any]:
    """
    Aplana un diccionario anidado.
    
    Args:
        data: Diccionario a aplanar
        parent_key: Clave padre (para recursión)
        sep: Separador para las claves
        
    Returns:
        Diccionario aplanado
    
    Examples:
        >>> flatten_dict({'a': {'b': 1, 'c': 2}})
        {'a.b': 1, 'a.c': 2}
    """
    items = []
    
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    
    return dict(items)


# ============================================================================
# UTILIDADES DE CÁLCULO
# ============================================================================

def calculate_percentage(
    part: Union[int, float],
    total: Union[int, float],
    decimals: int = 2
) -> float:
    """
    Calcula un porcentaje de forma segura.
    
    Args:
        part: Parte del total
        total: Total
        decimals: Decimales a redondear
        
    Returns:
        Porcentaje calculado (0-100)
    
    Examples:
        >>> calculate_percentage(25, 100)
        25.0
        >>> calculate_percentage(1, 3)
        33.33
        >>> calculate_percentage(10, 0)
        0.0
    """
    if total == 0:
        return 0.0
    
    percentage = (float(part) / float(total)) * 100
    return round(percentage, decimals)


def calculate_average(
    values: List[Union[int, float]],
    decimals: int = 2
) -> float:
    """
    Calcula el promedio de una lista de valores.
    
    Args:
        values: Lista de valores numéricos
        decimals: Decimales a redondear
        
    Returns:
        Promedio calculado
    
    Examples:
        >>> calculate_average([10, 20, 30])
        20.0
        >>> calculate_average([])
        0.0
    """
    if not values:
        return 0.0
    
    return round(sum(values) / len(values), decimals)


def clamp(
    value: Union[int, float],
    min_value: Union[int, float],
    max_value: Union[int, float]
) -> Union[int, float]:
    """
    Limita un valor entre un mínimo y máximo.
    
    Args:
        value: Valor a limitar
        min_value: Valor mínimo
        max_value: Valor máximo
        
    Returns:
        Valor limitado
    
    Examples:
        >>> clamp(15, 10, 20)
        15
        >>> clamp(5, 10, 20)
        10
        >>> clamp(25, 10, 20)
        20
    """
    return max(min_value, min(value, max_value))


# ============================================================================
# HELPERS DE LISTA Y COLECCIONES
# ============================================================================

def chunk_list(
    items: List[Any],
    chunk_size: int
) -> List[List[Any]]:
    """
    Divide una lista en chunks del tamaño especificado.
    
    Args:
        items: Lista a dividir
        chunk_size: Tamaño de cada chunk
        
    Returns:
        Lista de chunks
    
    Examples:
        >>> chunk_list([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
    """
    return [
        items[i:i + chunk_size] 
        for i in range(0, len(items), chunk_size)
    ]


def deduplicate_list(
    items: List[Any],
    key: Optional[callable] = None
) -> List[Any]:
    """
    Elimina duplicados de una lista preservando el orden.
    
    Args:
        items: Lista con posibles duplicados
        key: Función para extraer clave de comparación
        
    Returns:
        Lista sin duplicados
    
    Examples:
        >>> deduplicate_list([1, 2, 2, 3, 1])
        [1, 2, 3]
        >>> deduplicate_list([{'id': 1}, {'id': 2}, {'id': 1}], key=lambda x: x['id'])
        [{'id': 1}, {'id': 2}]
    """
    seen = set()
    result = []
    
    for item in items:
        item_key = key(item) if key else item
        
        if item_key not in seen:
            seen.add(item_key)
            result.append(item)
    
    return result


def group_by(
    items: List[Dict[str, Any]],
    key: str
) -> Dict[Any, List[Dict[str, Any]]]:
    """
    Agrupa una lista de diccionarios por una clave.
    
    Args:
        items: Lista de diccionarios
        key: Clave por la cual agrupar
        
    Returns:
        Diccionario con items agrupados
    
    Examples:
        >>> items = [{'dept': 'IT', 'name': 'Alice'}, {'dept': 'HR', 'name': 'Bob'}]
        >>> group_by(items, 'dept')
        {'IT': [{'dept': 'IT', 'name': 'Alice'}], 'HR': [{'dept': 'HR', 'name': 'Bob'}]}
    """
    groups = {}
    
    for item in items:
        group_key = item.get(key)
        
        if group_key not in groups:
            groups[group_key] = []
        
        groups[group_key].append(item)
    
    return groups


# ============================================================================
# UTILIDADES DE ESTADO Y ENUMS
# ============================================================================

ESTADO_COLORES = {
    "pendiente": "#FFA500",      # Naranja
    "en_progreso": "#2196F3",    # Azul
    "completado": "#4CAF50",     # Verde
    "aprobado": "#4CAF50",       # Verde
    "reprobado": "#F44336",      # Rojo
    "cancelado": "#9E9E9E",      # Gris
    "archivado": "#757575",      # Gris oscuro
    "borrador": "#9E9E9E",       # Gris
    "publicado": "#4CAF50",      # Verde
}


def get_estado_color(estado: str) -> str:
    """
    Obtiene el color asociado a un estado.
    
    Args:
        estado: Nombre del estado
        
    Returns:
        Código de color hexadecimal
    
    Examples:
        >>> get_estado_color('completado')
        '#4CAF50'
        >>> get_estado_color('desconocido')
        '#000000'
    """
    return ESTADO_COLORES.get(estado.lower(), "#000000")


def get_estado_badge(estado: str) -> Dict[str, str]:
    """
    Obtiene un badge con color y label para un estado.
    
    Args:
        estado: Nombre del estado
        
    Returns:
        Diccionario con color y label
    
    Examples:
        >>> get_estado_badge('completado')
        {'color': '#4CAF50', 'label': 'Completado'}
    """
    return {
        "color": get_estado_color(estado),
        "label": estado.replace('_', ' ').title()
    }
    