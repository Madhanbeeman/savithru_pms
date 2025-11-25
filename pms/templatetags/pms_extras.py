from django import template

register = template.Library()

# --- COLOR PALETTE (Light Background, Dark Text) ---
COLOR_PAIRS = [
    {'bg': '#e3f2fd', 'text': '#0d47a1'}, # Blue
    {'bg': '#f3e5f5', 'text': '#4a148c'}, # Purple
    {'bg': '#e8f5e9', 'text': '#1b5e20'}, # Green
    {'bg': '#fff3e0', 'text': '#e65100'}, # Orange
    {'bg': '#ffebee', 'text': '#b71c1c'}, # Red
    {'bg': '#e0f7fa', 'text': '#006064'}, # Cyan
    {'bg': '#fff8e1', 'text': '#ff6f00'}, # Amber
    {'bg': '#fce4ec', 'text': '#880e4f'}, # Pink
]

@register.filter
def get_user_bg_color(user_id):
    """Returns a light background color based on user ID."""
    if not user_id: return '#ffffff'
    index = user_id % len(COLOR_PAIRS)
    return COLOR_PAIRS[index]['bg']

@register.filter
def get_user_text_color(user_id):
    """Returns a dark text color based on user ID."""
    if not user_id: return '#000000'
    index = user_id % len(COLOR_PAIRS)
    return COLOR_PAIRS[index]['text']

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_attribute(obj, attr_name):
    return getattr(obj, attr_name, None)