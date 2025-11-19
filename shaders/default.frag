#version 330 core
out vec4 frag_color;

// These uniforms will come from your Material class
uniform vec3  u_color;       // Base color (RGB)
uniform vec3  u_emissive;    // Glow color (added on top)
uniform float u_alpha;       // Transparency (0.0–1.0)

void main()
{
    vec3 final_color = u_color + u_emissive;
    frag_color = vec4(final_color, u_alpha);
}