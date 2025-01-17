import sys
import traceback
import re
import os
import yaml

from ds.lever import Lever
from ds.scripts.detect_language import detect_language


class DescriptionBenefit(Lever):

    @Lever.log_generate
    def generate(self) -> None:
        text = self.input_dict['reference_description']
        self.input_dict['language'] = detect_language(text)

        ## Compliance
        additional_instructions, replacement_instructions = '', ''
        brand_id = self.input_dict.get('brand_id', '')
        compliance_file_path = 'ds/process/brand_specific/' + str(brand_id) + '.yaml'
        if os.path.exists(compliance_file_path):
            with open(compliance_file_path, "r") as f:
                data = yaml.safe_load(f) 
            additional_instructions = data.get('additional_instructions')
            replacement_instructions = data.get('replacement_instructions')

        self.prompt = [
            {
                "role" : "system",
                "content" : f'''You are a helpful digital marketing assistant. Use information from Brand, Article, Topic, and Benefit to write Creative Ads. Each Ad must be at least 12-15 words long.
{'Make sure Variations follow the following compliance guidelines.' + replacement_instructions if replacement_instructions else ''}'''.strip()
},

            {
                "role": "user", 
                "content": f'''###
Example 1
Brand: CoverWallet makes it easy for businesses to understand, buy and manage insurance. All online, in minutes. We make it simple, convenient, and fast for you to get the coverage you need at the right price.
Article:
1. We help your business by providing expert coverage recommendations and average pricing.
2. Get Quote online or talk to our helpful and professional advisors. Find the insurance you need.
Topic: "Cyber"
Benefit: Protection against Data Breach
Write 2 Descriptions for the Brand, Article, and Interest given above. Include Brand Name in each Ad.
1: Coverwallet's "Cyber" Insurance against Data Breach. Get free personalized quotes online or talk to our experts.
2: Protect your business from Data Breaches and Malware. Safeguard Against Hackers within minutes.

###
Example 2
Brand: VogueLooks is a brand specialising in Clothing and Apparel. Their products are designed with exceptional quality and showcase a confident style. Top Clothing and Apparel for every season.
Article:
1. Add an air of sophistication to your outfits with our trendy and fashionable collection.
2. Amazing Styles and Offers on VogueLooks.com! Buy 3 Get 2 Free on Clothing and Apparel.
Topic: "Suits"
Benefit: Professional, look more confident
Write 2 Descriptions for the Brand, Article, and Interest given above. Include Brand Name in each Ad.
1: Electrify your wardrobe with our premium "Suits", look more confident, and start turning heads. It's magic!
2: Look professional and Save on chic, elegant styles on VogeLooks.com. Buy 3 Get 2 Free on Everything!

###
Example 3
Brand: {self.input_dict['bu_detail']}
Article:
{self.input_dict['reference_description']}
Topic: "{self.input_dict['interest_keyword']}"
Benefit: {self.input_dict['benefit_used']}
Write 10 Descriptions for the Brand, Article, and Interest given above. Include Brand Name in each Ad.
All Descriptions must be in {self.input_dict['language']}.
{'Additional Instructions: ' + additional_instructions if additional_instructions else ''}
1:'''
            }]

        self.nlg_parameters = {
            "response_length": 400,
            "temperature": 0.7,
            "top_p": 1,
            "frequency_penalty": 1,
            "presence_penalty": 1,
            "stop": ["3.", "Article:", "Brand:", "\n\n"],
            "n" : 5
        }
        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)

    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations_list = [] 
        for generation in self.nlg_generations_list:
            t_gens = re.sub(r'\d+\s*[:\.]', '', generation)
            '''
            \d+ matches one or more digits, \s* matches zero or more whitespace characters, and [:\.] matches either a colon or a period. This pattern will replace the occurrence of a digit followed by an optional space and either a colon or a period in the generation string.
            '''
            t_gens = t_gens.split('\n')
            self.extracted_generations_list.extend(t_gens)
        return


    @Lever.log_postprocess
    def postprocess(self) -> None:
        if self.input_dict['language'] == 'English':
            post_process_obj = self.postprocess_class(title_case=False, ending_exclusions='!#', exclude_domain=True, exclude_phone_number=True)
            # TODO: + pass inputs to self.postprocess_class
            #       - fix long sentences
            #       - remove incomplete sentences
            #       - make domain lowercase

            self.post_process_list = []
            for generation in self.extracted_generations_list:
                self.post_process_list.append(post_process_obj.run(generation, input_dict=self.input_dict))
        else:
            self.post_process_list = self.extracted_generations_list
        return self.post_process_list

    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        filter_pipeline_obj = self.filter_generations_class(
            min_length=40, 
            max_length=90,
            filter_phrase=self.input_dict['benefit_used'])
        self.filter_generations_list, self.log_json['discard_filter_generations'] = filter_pipeline_obj.run(
            self.post_process_list, 
            self.input_dict['reference_description'],
            input_dict=self.input_dict,
            check_english= False if self.input_dict['language']!='English' else True)

        self.log_json['filtered_generations'] = self.filter_generations_list
        score_performance_obj = self.score_performance_class(brand_name=self.input_dict['bu_name'])
        self.performance_list = score_performance_obj.get_performance_scores(generations_list=self.filter_generations_list)
        cluster_text_obj = self.cluster_text_class(threshold=80)
        self.performance_generations_dict_list, self.log_json['discarded_low_performance_generations'] = cluster_text_obj.get_unique_assets_by_filter_key(input_assets=self.performance_list)


    @Lever.log_run       
    def run(self, input_dict):
        try:
            self.input_dict = input_dict
            no_of_outputs = self.input_dict['n_generations']

            self.generate()
            self.extract_label()
            self.postprocess()

            self.filter_generations()

            # TODO: + prepare output in desired format
            self.filter_generations_list = {
                'benefit': self.performance_generations_dict_list[:no_of_outputs]
            }
            return self.filter_generations_list, self.log_json
        except Exception as exc:
            _, _, exc_traceback = sys.exc_info()
            trace = traceback.format_tb(exc_traceback)
            updated_log_json = {"trace": trace, "exception":str(exc), "info": self.log_json}
            return {"benefit":[]}, updated_log_json
if __name__ == '__main__':
    # TODO: add prompt temptlate, params, support dict to csv for google

#     pt="""Use information from Brand, Article, Topic, and Benefit to write Creative Ads. Each Ad must be at least 12-15 words long.


# Brand: CoverWallet makes it easy for businesses to understand, buy and manage insurance. All online, in minutes. We make it simple, convenient, and fast for you to get the coverage you need at the right price.
# Article:
# 1. We help your business by providing expert coverage recommendations and average pricing.
# 2. Get Quote online or talk to our helpful and professional advisors. Find the insurance you need.
# Topic: "Cyber"
# Benefit: Protection against Data Breach
# ###
# 1: Coverwallet's "Cyber" Insurance. Get free personalized quotes online or talk to our experts.
# 2: Protect your business from Data Breaches and Malware. Safeguard Against Hackers within minutes.
# Brand: VogueLooks is a brand specialising in Clothing and Apparel. Their products are designed with exceptional quality and showcase a confident style. Top Clothing and Apparel for every season.
# Article:
# 1. Add an air of sophistication to your outfits with our trendy and fashionable collection.
# 2. Amazing Styles and Offers on VogueLooks.com! Buy 3 Get 2 Free on Clothing and Apparel.
# Topic: "Suits"
# Benefit: Professional, look more confident
# ###
# 1: Electrify your wardrobe with our premium "Suits" and start turning heads. It's magic!
# 2: Look professional and Save on chic, elegant styles on VogeLooks.com. Buy 3 Get 2 Free on Everything!
# Brand: At HomeLane, we bring together functionality and aesthetics to provide homeowners with customised and efficient home designs. Our designers specialise in home interior designs and home décor and help you create a personalized home to suit your lifestyle.
# Article:
# 1. Thousands of design experts. Your search for the best home interior brand ends here.
# 2. Book a free online consultation today. Renovate your dream home at Up to 23% Off on all Designs.
# Topic: "London"
# Benefit: Elegant and luxurious
# ###
# 1: Does a mix of Art Deco, Elegance and Luxury sound good? Try "London" Style Interior Designs!
# 2: Book a free online consultation with one of our 1000+ brilliant designers. Get Up to 23% Off on HomeLane.
# Brand: {self.input_dict['bu_detail']}
# Article:
# {self.input_dict['reference_description']}
# Topic: "{self.input_dict['interest_keyword']}"
# Benefit: {benefit_used}
# ###
# 1:"""

#     pp = {
#         'engine': 'text-davinci-001',
#         'response_length': 64,
#         'temperature': 0.7,
#         'top_p': 1,
#         'frequency_penalty': 1,
#         'presence_penalty': 1,
#         'stop_seq': ["3:"]
#     }
#     sd = {}

#     id = {
#         "bu_detail": "Carsome is the #1 online used car buying platform. Buyers can browse 50K pre-loved cars inspected on 175-point and get a 360-degree view of the car's interior and exterior, take a test drive, trade-in your old car, and get doorstep delivery. All cars come with a 1-year warranty, 5 days money-back guarantee, fixed price, and no hidden fees.",
#         "reference_description": "1. Buy pre-loved Cars. Carsome Certified Cars. 175-Point Inspection Checklist.\n2. Carsome's Certified Cars come with a 1-year warranty and a 5-Day money-back guarantee.",
#         "interest_keyword": "Family Car",
#         "bu_name": "Carsome",
#         "benefit_used": "Low cost",
#         "n_generations": 10,
#         "brand_id": "f226bd37-db7c-4908-b992-907ff441bcb7"
#     }

#     gens, rej_gens = DescriptionBenefit().run(input_dict=id)
#     print(gens)
#     print(len(gens['benefit']))

    # t = ["Find your perfect Family Car at Carsome. With our 175-point Inspection Checklist, you can be sure you're getting a high-quality car.", "Carsome's Family Cars come with a 1-year warranty and a 5-Day money-back guarantee.", "Carsome is the best place to buy a Family Car. With our 175-point Inspection Checklist, you can be sure you're getting a quality car.", 'All Carsome Certified Cars come with a 1-year warranty and a 5-Day money-back guarantee. Buy with confidence', "Drive with peace of mind. Carsome's Family Cars are reliable and safe.", 'With a 1-year warranty and a 5-Day money-back guarantee, Carsome is the best place to buy pre-loved cars.', 'Bring the family along for the ride with our Family Car options.', 'Carsome has a wide selection of family-friendly cars that are perfect for any budget.', "Carsome's Family Car Collection. Buy a pre-loved car with confidence. Comes with a 1-year warranty and a 5-Day money-back guarantee.", 'Get peace of mind with Carsome Certified Cars. 175-point Inspection Checklist.', "Looking for a Family Car? Check out Carsome's Certified Cars", "Carsome's Certified Cars come with a 1-year warranty and a 5-Day money-back guarantee.", 'Buy a reliable car for your family. Carsome has a wide range of certified family cars.', 'Get a 1-year warranty and a 5-Day money-back guarantee on all Carsome Certified Cars.', 'Drive with peace of mind. Carsome Certified Family Cars.', "Carsome's Certified Cars come with a 1-year warranty and a 5-Day money-back guarantee. 3. Buy with confidence. Shop Carsome Certified Family Cars now.", "Upgrade your family car today. Get a bigger and better car for your family's needs.", 'Carsome has a wide selection of family cars. Choose the perfect car for your family today.', 'Get a car that the whole family can enjoy. Carsome has got you covered.', 'Choose from a wide range of family cars. Carsome Certified Cars come with a 1-year warranty and a 5-Day money-back guarantee.']

    # filter_pipeline_obj = self.filter_generations_class(min_length=50, max_length=90)
    # filter_generations_list, filtered_generations = filter_pipeline_obj.run(t, id['reference_description'])
    # print('postprep', len(t), t)
    # print('filtered', len(filter_generations_list), filter_generations_list)


    id1 = {
        "bu_detail": "Semrush is an all-in-one tool suite for improving online visibility and discovering marketing insights. The tools and reports can help marketers with the following services: SEO, PPC, SMM, Keyword Research, Competitive Research, PR, Content Marketing, Marketing Insights, and Campaign Management.\n",
        "reference_description": "Research Your Competitors,The Ultimate 20-in-1 SEO Tool,{KeyWord Semrush SEO Tools}",
        "interest_keyword": "local",
        "bu_name": "Semrush",
        "benefit_used": "free",
        "n_generations": 5,
        "brand_id" : "6cdb2607-6c1f-4de2-b0a2-1e82172eccd9"
    }

    id2 = {
        "bu_detail": "Semrush is an all-in-one tool suite for improving online visibility and discovering marketing insights. The tools and reports can help marketers with the following services: SEO, PPC, SMM, Keyword Research, Competitive Research, PR, Content Marketing, Marketing Insights, and Campaign Management.\n",
        "reference_description": "Research Your Competitors,The Ultimate 20-in-1 SEO Tool,{KeyWord Semrush SEO Tools}",
        "interest_keyword": "local",
        "bu_name": "Semrush",
        "benefit_used": "free",
        "n_generations": 5,
        "brand_id" : "276cb088-ce1a-42f6-9ec7-867ee22ef70f"
    }

    id3 = {
        "bu_detail": "Mitte is a 3-in-1 watermaker that turns your tap water into purified, mineralized, still or sparkling water.",
        "reference_description": "1. Doubting Water Quality? Benefit From Superior Filtration With _Mitte_. Get Best Deals Today!\n2. Create Healthy Water, Personalized With Minerals. Best Price. Order From _Mitte_ Today!",
        "interest_keyword": "",
        "bu_name": "Mitte",
        "benefit_used": "Free RO",
        "usp_used": "Find Lost 401Ks",
        "n_generations": 5,
        "brand_id" : "6cdb2607-6c1f-4de2-b0a2-1e82172eccd9_"
    }

    outputs = []

    for id in [id1, id2, id3]:

        gens, rej_gens = DescriptionBenefit().run(input_dict=id)
        outputs.append("\n".join([gen['text'] for gen in gens['benefit']]))
        # print(len(gens['benefit']))

    for output in outputs:
        print("*****************************")
        print(output)