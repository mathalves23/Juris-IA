# Cenários de Teste - MVP do Editor IA

Este documento apresenta cenários de teste recomendados para validação do MVP do Editor IA, organizados por funcionalidade principal.

## 1. Autenticação e Acesso

### Cenário 1.1: Registro de novo usuário
1. Acesse a página inicial
2. Clique em "Registre-se"
3. Preencha os dados solicitados
4. Confirme o registro
5. Verifique se o acesso ao dashboard é concedido

### Cenário 1.2: Login de usuário existente
1. Acesse a página inicial
2. Insira credenciais válidas
3. Verifique se o acesso ao dashboard é concedido

## 2. Criação e Edição de Documentos

### Cenário 2.1: Criar documento em branco
1. No dashboard, clique em "Novo Documento"
2. Selecione "Documento em branco"
3. Digite um título
4. Adicione conteúdo ao editor
5. Salve como rascunho
6. Verifique se o documento aparece na lista de documentos

### Cenário 2.2: Criar documento a partir de modelo
1. No dashboard, clique em "Usar Modelo"
2. Selecione um modelo da lista
3. Personalize o conteúdo
4. Salve como rascunho
5. Verifique se o documento aparece na lista de documentos

### Cenário 2.3: Editar documento existente
1. Acesse a lista de documentos
2. Selecione um documento existente
3. Modifique o conteúdo
4. Salve as alterações
5. Verifique se as alterações foram mantidas ao reabrir o documento

### Cenário 2.4: Finalizar documento
1. Abra um documento em modo de edição
2. Faça as alterações necessárias
3. Clique em "Finalizar"
4. Verifique se o status do documento mudou para "Finalizado"

## 3. Uso da Assistência IA

### Cenário 3.1: Gerar texto com IA
1. Durante a edição de um documento, clique em "Assistente IA"
2. Digite uma instrução clara (ex: "Escreva uma introdução sobre responsabilidade civil")
3. Clique em "Gerar texto"
4. Avalie a qualidade e relevância do texto gerado
5. Clique em "Inserir no documento"
6. Verifique se o texto foi inserido corretamente

### Cenário 3.2: Criar documento completo com IA
1. No dashboard, clique em "Novo Documento"
2. Selecione "Gerar com IA"
3. Forneça instruções detalhadas sobre o documento desejado
4. Avalie o documento gerado
5. Faça ajustes necessários
6. Salve o documento

## 4. Gestão de Modelos

### Cenário 4.1: Criar novo modelo
1. Acesse a seção "Modelos"
2. Clique em "Novo Modelo"
3. Defina nome e categoria
4. Adicione conteúdo ao editor
5. Clique em "Extrair Variáveis"
6. Verifique se as variáveis foram detectadas corretamente
7. Salve o modelo
8. Verifique se o modelo aparece na lista

### Cenário 4.2: Usar modelo para criar documento
1. Acesse a seção "Modelos"
2. Localize um modelo específico
3. Clique em "Usar"
4. Verifique se o conteúdo do modelo foi carregado corretamente
5. Personalize o documento
6. Salve como novo documento

## 5. Versionamento de Documentos

### Cenário 5.1: Verificar histórico de versões
1. Abra um documento que já foi editado múltiplas vezes
2. Clique em "Versões"
3. Verifique se as versões anteriores estão listadas com datas corretas

### Cenário 5.2: Restaurar versão anterior
1. Abra um documento com múltiplas versões
2. Clique em "Versões"
3. Selecione uma versão anterior
4. Clique em "Restaurar"
5. Verifique se o conteúdo foi restaurado corretamente

## 6. Controle de Uso (Plano Editor IA)

### Cenário 6.1: Verificar limite de documentos
1. Acesse o dashboard
2. Verifique o contador de documentos utilizados/limite
3. Crie um novo documento
4. Confirme que o contador foi atualizado

### Cenário 6.2: Comportamento ao atingir limite
1. Em uma conta que esteja próxima do limite de documentos
2. Tente criar um novo documento após atingir o limite
3. Verifique se a mensagem de limite atingido é exibida
4. Confirme que a opção de upgrade é oferecida

## Observações para Teste

Durante os testes, observe e registre:

1. **Desempenho**: Tempo de resposta para operações comuns
2. **Usabilidade**: Facilidade de navegação e compreensão das funcionalidades
3. **Qualidade da IA**: Precisão e relevância do texto gerado
4. **Estabilidade**: Ocorrência de erros ou comportamentos inesperados
5. **Experiência geral**: Impressões sobre o fluxo de trabalho e produtividade

Seus comentários sobre estes aspectos serão valiosos para aprimorarmos o produto.
