import os


# Parse URL replacements into array of pairs
def get_url_replace_pairs():
    url_replace_pairs = []
    URL_REPLACES = os.environ.get("URL_REPLACES", "")
    if URL_REPLACES:
        # Split by semicolon to get multiple replacements
        replacements = URL_REPLACES.split(';')
        for replacement in replacements:
            if '=>' in replacement:
                original, new = replacement.strip().split('=>')
                url_replace_pairs.append((original.strip(), new.strip()))
    return url_replace_pairs

url_replace_pairs = get_url_replace_pairs()

def url_replace(images):
    # Replace URLs based on url_replace_pairs
    if not url_replace_pairs:
        return False
    
    for image in images:
        for original, new in url_replace_pairs:
            if original in image.get('url'):
                image['url'] = image['url'].replace(original, new)
    return True
