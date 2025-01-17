
#Import our own files
from ds.levers.uac.uac_v2_api import AssetApiCalls
from ds.levers.uac.uac_theme import UACThemeGeneration
from ds.levers.uac.uac_v2_headline import UACHeadlineGeneration
from ds.levers.uac.uac_v2_description import UACDescriptionGeneration


def generate_themes(input_headlines, input_descriptions):

    input_assets = '\n'.join(input_headlines + input_descriptions)

    generations, _ = UACThemeGeneration().run({
            "input_assets" : input_assets
        })
    return generations

def generate_headlines_theme(brand, input_themes):

    generations, _ = UACHeadlineGeneration().run(
        input_dict = {
            "bu_detail" : brand,
            "input_themes" : input_themes
        })
    return generations
    
#label_extracted, post_process_list, length_list, duplicate_list,filtered_list 

def generate_headlines_interest(brand, input_themes):

    generations, label_extracted, post_process_list, length_list, duplicate_list,filtered_list = UACHeadlineGeneration().run({
            "bu_detail" : brand,
            "input_themes" : input_themes
        })
    return generations, label_extracted, post_process_list, length_list, duplicate_list,filtered_list 

def generate_descriptions(brand, input_themes):

    generations, _ = UACDescriptionGeneration().run({
            "bu_detail" : brand,
            "input_themes" : input_themes
        })
    return generations

def generate(ad_account_id, ad_group_id, brand):
    input_headlines, input_descriptions = AssetApiCalls(ad_account_id,ad_group_id).execute()
    themes = generate_themes(input_headlines, input_descriptions)
    print(themes)
    input_themes = " ,".join(themes)
    #generations, label_extracted, post_process_list, length_list, duplicate_list,filtered_list = generate_headlines_theme(brand , input_themes)
    headlines = generate_headlines_theme(brand , input_themes)
    for input in input_headlines:
        if input in headlines:
            headlines.remove(input)
    descriptions = generate_descriptions(brand , input_themes)
    for input in input_descriptions:
        if input in descriptions:
            descriptions.remove(input)
    return themes,input_headlines, input_descriptions, headlines, descriptions

def generated_themes(ad_account_id, ad_group_id):
    input_headlines, input_descriptions = AssetApiCalls(ad_account_id,ad_group_id).execute()
    themes = generate_themes(input_headlines, input_descriptions)
    return themes,input_headlines, input_descriptions
    
def generated_outputs(brand, theme):
    generations, label_extracted, post_process_list, length_list, duplicate_list,filtered_list = generate_headlines_interest(brand , theme)
    return generations, label_extracted, post_process_list, length_list, duplicate_list,filtered_list

if __name__ == '__main__':
    ad_account_id = 1272161627
    ad_group_id = 134012211981
    # brand = "Goibibo is India’s leading online travel booking brand providing range of choice for hotels, flights, trains, bus and cars for travelers. Our core value differentiator is the most trusted user experience, be it in terms of quickest search and booking, fastest payments, settlement or refund processes."

    # themes, generations, input_headlines, input_descriptions = generate(ad_account_id, ad_group_id, brand)
    # print(generations)


    input_headlines, input_descriptions = AssetApiCalls(ad_account_id,ad_group_id).execute()