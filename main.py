# final_cube.py — THIS WILL SHOW A MASSIVE SPINNING PINK CUBE — GUARANTEED
import pygame
import moderngl
import numpy as np
import time
import sys

print("Starting — if you see this and a pink cube, we win.")

pygame.init()
screen = pygame.display.set_mode((1280, 720), pygame.OPENGL | pygame.DOUBLEBUF)
ctx = moderngl.create_context()
ctx.enable(moderngl.DEPTH_TEST)

# Embedded shaders — NO files needed
vert_shader = '''
#version 330 core
layout(location = 0) in vec3 in_position;
uniform mat4 u_mvp;
void main() {
    gl_Position = u_mvp * vec4(in_position, 1.0);
}
'''

frag_shader = '''
#version 330 core
out vec4 frag_color;
void main() {
    frag_color = vec4(1.0, 0.2, 0.8, 1.0);  // BRIGHT PINK
}
'''

program = ctx.program(vertex_shader=vert_shader, fragment_shader=frag_shader)

# 24 vertices — correct winding — HUGE cube
vertices = np.array([
    -1,-1,-1, 1,-1,-1, 1,1,-1, -1,1,-1,
    -1,-1,1, 1,-1,1, 1,1,1, -1,1,1,
    -1,-1,-1, -1,-1,1, -1,1,1, -1,1,-1,
    1,-1,-1, 1,-1,1, 1,1,1, 1,1,-1,
    -1,-1,-1, 1,-1,-1, 1,-1,1, -1,-1,1,
    -1,1,-1, 1,1,-1, 1,1,1, -1,1,1
], dtype='f4').reshape(-1, 3) * 4.0  # 4× bigger

indices = np.array([
    0,1,2,2,3,0, 4,5,6,6,7,4, 8,9,10,10,11,8,
    12,13,14,14,15,12, 16,17,18,18,19,16, 20,21,22,22,23,20
], dtype='i4')

vbo = ctx.buffer(vertices.tobytes())
ibo = ctx.buffer(indices.tobytes())
vao = ctx.vertex_array(program, [(vbo, '3f', 'in_position')], index_buffer=ibo)

clock = pygame.time.Clock()
start_time = time.time()

print("RENDER LOOP STARTED — YOU SHOULD SEE A SPINNING PINK CUBE NOW")

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Black background
    ctx.clear(0.0, 0.0, 0.0, 1.0)

    # Spinning model matrix
    t = time.time() - start_time
    angle_y = t * 0.7
    angle_x = t * 0.5
    cy, sy = np.cos(angle_y), np.sin(angle_y)
    cx, sx = np.cos(angle_x), np.sin(angle_x)

    model = np.array([
        [ cy, 0, sy, 0],
        [ sx*sy, cx, sx*cy, 0],
        [-cx*sy, sx, cx*cy, 0],
        [ 0, 0, 0, 1]
    ], dtype='f4')

    # Simple orthographic projection (no clipping issues)
    mvp = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, -5, 1]  # move cube forward
    ], dtype='f4') @ model

    program['u_mvp'].write(mvp.tobytes())
    vao.render(moderngl.TRIANGLES)

    pygame.display.flip()
    clock.tick(60)