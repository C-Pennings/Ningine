import pygame, json, moderngl

def path_to_tex(path):
    return surf_to_tex(path_to_surf(path))

def surf_to_tex(surf, ctx, rgba=True, flip_y=False):
    fmt = "RGBA" if rgba else "RGB"
    if rgba:
        surf = surf.convert_alpha()
    else:
        surf = surf.convert()

    if flip_y:
        surf = pygame.transform.flip(surf, False, True)

    w, h = surf.get_size()
    data = pygame.image.tostring(surf, fmt, False)
    components = 4 if rgba else 3
    tex = ctx.texture((w, h), components, data)
    tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
    try:
        tex.repeat_x = False
        tex.repeat_y = False
    except Exception:
        pass
    return tex

def path_to_surf(path):
    try:
        img = pygame.image.load(path)
        return img
    except:
        pass

def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_json(path, dict):
    try:
        with open(path, 'w') as f:
            json.dump(dict, f)
    except:
        pass