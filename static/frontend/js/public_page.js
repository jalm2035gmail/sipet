    (function(){
      var links = document.querySelectorAll('[data-sipet-auth-link]');
      if(!links.length) return;
      fetch('/api/backend/me', {credentials:'include'})
        .then(function(r){ return r.ok ? r.json() : null; })
        .then(function(data){
          var authenticated = !!(data && data.authenticated);
          var username = authenticated ? String(data.username || data.user_name || '').trim() : '';
          var imageUrl = authenticated ? String(data.image_url || data.imagen || '').trim() : '';
          links.forEach(function(link){
            var label = link.querySelector('[data-sipet-auth-label]');
            var avatar = link.querySelector('[data-sipet-auth-avatar]');
            var accessibleLabel = authenticated ? 'Abrir panel' : 'Ingresar';
            var targetHref = authenticated ? String(data.panel_url || '/inicio').trim() || '/inicio' : '/backend/login';
            if(label){
              label.textContent = authenticated ? (username || accessibleLabel) : accessibleLabel;
            }
            if (avatar) {
              if (authenticated && imageUrl) {
                avatar.src = imageUrl;
                avatar.alt = username || accessibleLabel;
                link.classList.add('is-user-image');
              } else {
                avatar.removeAttribute('src');
                avatar.alt = '';
                link.classList.remove('is-user-image');
              }
            }
            link.setAttribute('href', targetHref);
            link.setAttribute('title', authenticated ? 'Abrir panel del backend' : accessibleLabel);
            link.setAttribute('aria-label', authenticated ? 'Abrir panel del backend' : accessibleLabel);
          });
        })
        .catch(function(){});
    })();
