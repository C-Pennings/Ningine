#version 330 core
layout(location = 0) in vec3 in_position;
uniform mat4 u_proj;
uniform mat4 u_view;
uniform mat4 u_model; // will be identity from CPU
uniform float u_time;
void main() {
    float a = u_time * 0.5;
    float c = cos(a);
    float s = sin(a);
    mat4 rot = mat4(
        vec4( c, 0.0,  s, 0.0),
        vec4(0.0, 1.0, 0.0, 0.0),
        vec4(-s, 0.0,  c, 0.0),
        vec4(0.0, 0.0, 0.0, 1.0)
    );
    gl_Position = u_proj * u_view * (u_model * rot) * vec4(in_position, 1.0);
}