#include <stdio.h>
#include <string.h>

typedef struct {
    int id_evento;
    char nome[50];
    int capacidade_maxima;
    int vagas_ocupadas;
    char status[20];
} Evento;


void buscar_por_id(Evento eventos[], int tamanho, int id_procurado) {
    for (int i = 0; i < tamanho; i++) {
        if (eventos[i].id_evento == id_procurado) {
            printf("{'id_evento': %d, 'nome': '%s', 'capacidade_maxima': %d, 'vagas_ocupadas': %d, 'status': '%s'}\n", 
                   eventos[i].id_evento, eventos[i].nome, eventos[i].capacidade_maxima, eventos[i].vagas_ocupadas, eventos[i].status);
            return;
        }
    }
    printf("Evento nao encontrado\n");
}

int main() {
    
    Evento eventos[2] = {
        {101, "Show de Rock", 500, 450, "Disponivel"},
        {102, "Palestra Tech", 200, 200, "Esgotado"}
    };

    printf("=== LISTAGEM DE EVENTOS ===\n");
    for (int i = 0; i < 2; i++) {
        printf("{'id_evento': %d, 'nome': '%s', 'capacidade_maxima': %d, 'vagas_ocupadas': %d, 'status': '%s'}\n", 
               eventos[i].id_evento, eventos[i].nome, eventos[i].capacidade_maxima, eventos[i].vagas_ocupadas, eventos[i].status);
    }

    printf("\n=== BUSCA POR ID (102) ===\n");
    buscar_por_id(eventos, 2, 102);

    return 0;
}