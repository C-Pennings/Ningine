#version 330 core

out vec4 frag_color;

// THESE MUST MATCH EXACTLY what your Material.bind() sends
uniform vec3 u_color;
uniform vec3 u_emissive;
uniform float u_alpha;

void main()
{
    vec3 final_color = u_color + u_emissive;
    frag_color = vec4(final_color, u_alpha);
}