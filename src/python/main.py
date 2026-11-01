def buscar_por_id(eventos, id_procurado):
    for evento in eventos:
        if evento["id_evento"] == id_procurado:
            return evento
    return None

eventos = [
    {"id_evento": 101, "nome": "Show de Rock", "capacidade_maxima": 500, "vagas_ocupadas": 450, "status": "Aberto"},
    {"id_evento": 102, "nome": "Palestra Tech", "capacidade_maxima": 200, "vagas_ocupadas": 200, "status": "Esgotado"}
]

print("=== LISTAGEM DE EVENTOS ===")
for evento in eventos:
    print(evento)

print("\n=== BUSCA POR ID (102) ===")
resultado = buscar_por_id(eventos, 102)
print(resultado if resultado else "Evento não encontrado")