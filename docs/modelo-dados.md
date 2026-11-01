# Modelo de Dados

## Entidade
Evento

## Finalidade
Entidade Principal
Representa os eventos gerados para controle de inscrições e gestão da capacidade de atendimento.

## Atributos
- id_evento: Identificador numérico único do evento.
- nome: Nome ou setor do evento.
- capacidade_maxima: Número fixo de vagas/lugares disponíveis.
- vagas_ocupadas: Número de inscrições já confirmadas.
- status: Estado atual do evento (Disponível, Esgotado).

## Operações
- cadastrar(id, nome, capacidade)
- buscar_por_id(id)
- listar_todos()
- registrar_inscricao(id_evento, id_participante)

## Regras / invariantes
1. O número de `vagas_ocupadas` nunca pode ser superior à `capacidade_maxima`.
2. Quando as vagas chegam a 0 (zero), o `status` do evento muda automaticamente para "Esgotado".

## Operação provavelmente frequente
buscar_por_id
justificativa: É a operação mais crítica, pois o sistema precisa de localizar rapidamente um evento pelo seu código para processar qualquer nova inscrição ou verificar a lista de espera.