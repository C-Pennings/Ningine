#version 330 core

in vec3 in_position;

// The view-projection matrix without translation
uniform mat4 u_view_projection_matrix; 

out vec3 eyeDirection;

void main() {
    eyeDirection = in_position;
    // Map to clip space, ensuring z is always 1.0 (max depth)
    vec4 pos = u_view_projection_matrix * vec4(in_position, 1.0);
    gl_Position = pos.xyww; // Force z to max depth
}
