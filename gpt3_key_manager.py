import os
from dotenv import load_dotenv
load_dotenv()

def get_gpt3_key(rotate=False):
    """
    Function to retrive API keys from openai from optimal organisation
        to have minimal rate limit errors 
    """
    if rotate:
        if os.getenv('temp_key') == os.getenv('key1'):
            os.environ['temp_key'] = os.getenv('key2')
            os.environ['temp_org'] = os.getenv('org2')

        elif os.getenv('temp_key') == os.getenv('key2'):
            os.environ['temp_key'] = os.getenv('key3')
            os.environ['temp_org'] = os.getenv('org3')

        elif os.getenv('temp_key') == os.getenv('key3'):
            os.environ['temp_key'] = os.getenv('key4')
            os.environ['temp_org'] = os.getenv('org4')

        elif os.getenv('temp_key') == os.getenv('key4'):
            os.environ['temp_key'] = os.getenv('key1')
            os.environ['temp_org'] = os.getenv('org1')

    if not os.getenv('temp_key'):
        os.environ['temp_key'] = os.getenv('key1')
        os.environ['temp_org'] = os.getenv('org1')

    api_key = os.getenv('temp_key')
    org_key = os.getenv('temp_org')

    print("retrived : ", api_key, org_key)
    return api_key, org_key

    

    
