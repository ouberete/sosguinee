from django import template
from django.conf import settings
from django.templatetags.static import static
import os

register = template.Library()

@register.simple_tag
def responsive_image(path, size='medium'):
    # Définition des tailles d'images
    sizes = {
        'small': '300w',
        'medium': '800w',
        'large': '1200w'
    }
    
    # Générer le nom de fichier pour les différentes tailles
    base_name, ext = os.path.splitext(path)
    srcset = []
    
    for size_name, width in sizes.items():
        img_path = f"{base_name}-{size_name}{ext}"
        if os.path.exists(os.path.join(settings.STATIC_ROOT, img_path.lstrip('/'))):
            srcset.append(f"{static(img_path)} {width}")
    
    srcset_attr = ', '.join(srcset)
    return f'srcset="{srcset_attr}"'

@register.simple_tag
def lazy_image(path, alt='', classes=''):
    return f'''
        <img src="{static('img/placeholder.png')}"
             data-src="{static(path)}"
             alt="{alt}"
             class="lazyload {classes}"
             loading="lazy">
    '''