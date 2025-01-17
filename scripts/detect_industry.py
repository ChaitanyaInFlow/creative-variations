import os
import requests
from google.cloud import language_v1

class DetectIndustry:


    def __init__(self, credentails_path="ds/config/google_cred.json"):

        self.googleClassifierClient = language_v1.LanguageServiceClient.from_service_account_json(
            credentails_path)

    def get_class(self, text):
        clean_text = text
        category_scores = {}
        try:
            document = language_v1.Document(
                content=clean_text, type=language_v1.Document.Type.PLAIN_TEXT)
            response = self.googleClassifierClient.classify_text(
                request={'document': document})
            categories = response.categories
            category_scores = {}
            for category in categories:
                if category.confidence:
                    category_scores[category.name.split('/')[1]] = category.confidence
            if (len(category_scores) == 0) and (len(categories) > 0):
                category = categories[0]
                category_scores[category.name.split('/')[1]] = category.confidence

        except Exception as e:
            print('Error while finding category for brand : %s' % str(e))
            print(e)
            print('Input text to google classifier : ', clean_text)
        return category_scores

    def get_brand_description(self, search_term, country='us'):
        serp_api_url = 'https://serpapi.com/search'
        serp_api_key = ''
        search_params = {
            'api_key': serp_api_key,
            'engine': 'google', 
            'gl': 'us', 
            'hl': 'en'
            }
        search_params['q'] = search_term
        search_params['gl'] = country.lower()
        
        try:
            response = requests.get(serp_api_url, params=search_params)
            json_response = response.json()
            return "\n".join([result['snippet'] for result in json_response['organic_results']])[:500]
        except Exception as e:
            print('Error while retrieving search info %s' % e)
            return ''

    def get_industry(self, brand_name,brand_description=''):
        if brand_description == '':
            brand_description = self.get_brand_description(brand_name)
        brand_description = brand_description.strip()
        if len(brand_description.split(' '))<20:
            brand_description += ''.join(['\n'+brand_description] * int(20/len(brand_description.split(' '))))
        industry_dict = self.get_class(brand_description)
        print(industry_dict)
        if industry_dict:
            industry = max(industry_dict, key=lambda x: industry_dict[x])
        else:
            industry = ""
        return industry

    def get_perf_industry(self, brand_name, brand_description=''):
        industry_category_mapping_dict = {
            "Adult": "Others",
            "Arts & Entertainment": "Media",
            "Autos & Vehicles": "Automotive",
            "Beauty & Fitness": "Lifestyle",
            "Books & Literature": "Media",
            "Business & Industrial": "Others",
            "Computers & Electronics": "IT",
            "Finance": "Finance",
            "Food & Drink": "Food and Grocery",
            "Games": "Others",
            "Health": "Healthcare",
            "Hobbies & Leisure": "Lifestyle",
            "Home & Garden": "Lifestyle",
            "Internet & Telecom": "IT",
            "Jobs & Education": "Education",
            "Law & Government": "Others",
            "News": "Others",
            "Online Communities": "Others",
            "People & Society": "Others",
            "Pets & Animals": "Others",
            "Real Estate": "Others",
            "Reference": "Others",
            "Science": "Others",
            "Sensitive Subjects": "Others",
            "Shopping": "Apparel",
            "Sports": "Others",
            "Travel": "Lifestyle"
        }
        industry = self.get_industry(brand_name=brand_name, brand_description=brand_description) 
        return industry_category_mapping_dict.get(industry,"")
 
if __name__ == '__main__':
    import pandas as pd
