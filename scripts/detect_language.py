from google.cloud import translate_v2 as translate
translate_client = translate.Client.from_service_account_json('ds/config/google_cred.json')

def detect_language(text):
    language = translate_client.detect_language(text).get('language')
    if language == 'ms':
        return 'Malay'
    elif language == 'th':
        return 'Thai'
    elif language == 'es':
        return 'Spanish'
    elif language == 'da':
        return 'Danish'
    elif language == 'pt':
        return 'Portuguese'
    else:
        return 'English'
    

if __name__ == '__main__':

    #text = "Estrena millones de productos este Hot Sale a meses, sin tarjeta, sin aval con tu Crédito Claro Shop :fire::fire: Disfruta 15% de descuento adicional en tu primer compra + hasta 24 meses :star-struck:"

    text = "Quer milhas, cashback, desconto na fatura, cashback no Inter Shop ou investimento? Acumule pontos e escolha o seu com o Loop"

    language = translate_client.detect_language(text).get('language')

    print('LANGUAGE = ', language)
