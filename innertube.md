Aqui está um comando curl que replica exatamente uma chamada real para a API InnerTube (especificamente o endpoint de Busca), utilizando as configurações do cliente WEB encontradas no código fonte da biblioteca innertube.

Esta requisição vai diretamente para os servidores do Google (youtubei.googleapis.com), sem passar por proxies intermediários, simulando o comportamento de um navegador Desktop.

Comando CURL (Endpoint de Busca)
curl -X POST "https://youtubei.googleapis.com/youtubei/v1/search?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8&prettyPrint=false" \

-H "Content-Type: application/json" \

-H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36" \

-H "Referer: https://www.youtube.com/" \

-H "X-Goog-Api-Format-Version: 1" \

-H "X-YouTube-Client-Name: 1" \

-H "X-YouTube-Client-Version: 2.20250626.01.00" \

-H "Origin: https://www.youtube.com" \

-d '{

"context": {

"client": {

"clientName": "WEB",

"clientVersion": "2.20250626.01.00",

"hl": "pt",

"gl": "BR"

}

},

"query": "innertube api python"

}'

Explicação dos Parâmetros (Baseado no Código Fonte)
Para montar essa requisição, utilizei os dados extraídos diretamente dos arquivos config.py e models.py da biblioteca innertube (autor tombulled), que é a base para o funcionamento da API:

URL e API Key (config.py):
Base URL: https://youtubei.googleapis.com/youtubei/v1/
API Key: AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8. Esta é a chave pública padrão utilizada pelo cliente Web do YouTube.
Headers (models.py):
X-YouTube-Client-Name: 1: O ID 1 representa o cliente WEB.
X-YouTube-Client-Version: Deve corresponder à versão enviada no corpo do JSON (2.20250626.01.00). Se houver incompatibilidade, a API pode rejeitar a chamada.
Referer: Obrigatório ser https://www.youtube.com/ para o cliente WEB, caso contrário o Google bloqueia por CORS ou validação de origem.
Corpo JSON (context):
A API InnerTube exige um objeto context em todas as requisições.
clientName: Define qual "experiência" o YouTube deve entregar (WEB, ANDROID, IOS, etc.).
hl (Host Language) e gl (Geo Location): Definem o idioma e a região dos resultados (no exemplo usei pt e BR).
Outros Clientes
Se você quiser simular um dispositivo Android (o que geralmente retorna dados diferentes ou mais permissivos para certas mídias), altere os seguintes campos baseados no config.py:

API Key: AIzaSyA8eiZmM1FaDVjRy-df2KTyQ_vz_yYM39w
Client Name: ANDROID
Client Version: 19.17.34
X-YouTube-Client-Name: 3


---



Para obter apenas o transcript (legendas), o processo é um pouco mais complexo do que a busca. A API InnerTube não permite pedir o transcript diretamente usando apenas o ID do vídeo; você precisa de um token específico (chamado params) que é gerado dinamicamente quando você carrega a página do vídeo.

Portanto, para replicar a chamada real via curl, são necessários dois passos:

Chamar o endpoint next para obter o token params.
Chamar o endpoint get_transcript usando esse token.
Aqui estão os comandos curl e a explicação de como extrair o dado necessário:

Passo 1: Obter o token params (Endpoint next)
Esta chamada simula o carregamento da página do vídeo. Substitua ID_DO_VIDEO pelo ID real (ex: dQw4w9WgXcQ).

curl -X POST "https://youtubei.googleapis.com/youtubei/v1/next?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8" \

-H "Content-Type: application/json" \

-H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36" \

-H "Referer: https://www.youtube.com/watch?v=ID_DO_VIDEO" \

-H "X-YouTube-Client-Name: 1" \

-H "X-YouTube-Client-Version: 2.20250626.01.00" \

-d '{

"context": {

"client": {

"clientName": "WEB",

"clientVersion": "2.20250626.01.00",

"hl": "pt",

"gl": "BR"

}

},

"videoId": "ID_DO_VIDEO"

}'

Onde encontrar o token na resposta JSON: Você precisará procurar dentro da estrutura engagementPanels. O caminho específico no JSON, conforme documentado nos exemplos da biblioteca, é: engagementPanels -> (procure o item com panelIdentifier = "engagement-panel-searchable-transcript") -> engagementPanelSectionListRenderer -> content -> continuationItemRenderer -> continuationEndpoint -> getTranscriptEndpoint -> params.

Copie essa string longa do campo params.

Passo 2: Baixar o Transcript (Endpoint get_transcript)
Agora, use o valor copiado no campo params abaixo.

curl -X POST "https://youtubei.googleapis.com/youtubei/v1/get_transcript?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8" \

-H "Content-Type: application/json" \

-H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36" \

-H "Referer: https://www.youtube.com/watch?v=ID_DO_VIDEO" \

-H "X-YouTube-Client-Name: 1" \

-H "X-YouTube-Client-Version: 2.20250626.01.00" \

-d '{

"context": {

"client": {

"clientName": "WEB",

"clientVersion": "2.20250626.01.00",

"hl": "pt",

"gl": "BR"

}

},

"params": "COLE_O_VALOR_DO_PARAMS_AQUI"

}'

A resposta conterá um objeto JSON com actions -> updateEngagementPanelAction -> content -> transcriptRenderer, onde estarão os segmentos de texto e tempo.

Alternativa via Python (Automatizada)
Como fazer isso manualmente via curl é trabalhoso devido à extração do JSON aninhado, a biblioteca innertube possui um exemplo pronto que faz exatamente esse fluxo.

Baseado no arquivo examples/get-video-transcript.py:

from innertube import InnerTube



# Inicializa o cliente WEB

client = InnerTube("WEB")



video_id = "ID_DO_VIDEO"



# 1. Chama o endpoint 'next'

data = client.next(video_id)



# 2. Lógica para extrair o token 'params' automaticamente

params = None

engagement_panels = data.get("engagementPanels", [])

for panel in engagement_panels:

section = panel.get("engagementPanelSectionListRenderer", {})

if section.get("panelIdentifier") == "engagement-panel-searchable-transcript":

params = section["content"]["continuationItemRenderer"] \

["continuationEndpoint"]["getTranscriptEndpoint"]["params"]

break



if params:

# 3. Chama o endpoint 'get_transcript'

transcript = client.get_transcript(params)



# 4. Imprime o texto

segments = transcript["actions"]["updateEngagementPanelAction"] \

["content"]["transcriptRenderer"]["content"] \

["transcriptSearchPanelRenderer"]["body"] \

["transcriptSegmentListRenderer"]["initialSegments"]



for segment in segments:

text = segment["transcriptSegmentRenderer"]["snippet"]["runs"]["text"]

print(text)

else:

print("Transcript não encontrado ou indisponível.")

