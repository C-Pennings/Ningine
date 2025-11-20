#version 330 core

in vec3 eyeDirection;

uniform samplerCube u_skybox;

out vec4 fragmentColor;

void main() {
    fragmentColor = texture(u_skybox, eyeDirection);
}
