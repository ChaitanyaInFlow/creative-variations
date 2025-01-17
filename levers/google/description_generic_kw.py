import sys
import traceback
import math

from ds.lever import Lever

class DescriptionGenericKeyword(Lever):

    @Lever.log_generate
    def generate(self) -> None:
        brand_name = self.input_dict['bu_name']
        brand_detail = self.input_dict['bu_detail']
        article = self.input_dict['reference_description']

        if brand_detail.lower().split()[0] in brand_name.lower().split():
            brand_name = brand_name
            brand_detail = brand_detail.replace(brand_name, f"_{brand_name}_")
        else:
            brand_name = brand_detail.split()[0]
            brand_detail = brand_detail.replace(brand_name, f"_{brand_name}_")

        article = article.replace(brand_name, f"_{brand_name}_")

        self.input_dict['bu_detail'] = brand_detail
        self.input_dict['reference_description'] = article

        self.prompt = [{
                "role": "user", 
                "content": f'''Rephrase the given Article to write Creative Google Ads for the given Brand, Article, and Interest Keyword. Each Ad must be at least 12-15 words long.
###
Example 1
Brand: CoverWallet makes it easy for businesses to understand, buy and manage insurance. All online, in minutes. We make it simple, convenient, and fast for you to get the coverage you need at the right price.
Article:
1. We help your business by providing expert coverage recommendations and average pricing.
2. Get Quote online or talk to our helpful and professional advisors. Find the insurance you need.
Interest Keyword: "insurance against cyber crime"
Write 3 Descriptions for the Brand, Article, and Interest given above. Include Brand Name in each Ad.
Ad 1: Protect your business from Data Breaches and Malware in minutes with CoverWallet.
Ad 2: Find the right protection against Hackers at the right price with CoverWallet. In Minutes.
Ad 3: Talk to CoverWallet experts for information about the right coverage for your business needs.

###
Example 2
Brand: HomeLane is a home interior company that helps homeowners do their home interiors in a personalized and pocket-friendly way. Explore thousands of inspiring interior designs or get a free estimate.
Article:
1. Thousands of design experts. Your search for the best home interior brand ends here.
2. Book a free online consultation today. Renovate your dream home at Up to 23% Off on all Designs.
Interest Keyword: "trendy London style interiors 2020"
Write 4 Descriptions for the Brand, Article, and Interest given above. Include Brand Name in each Ad.
Ad 1: Modern Aesthetic Interior Designs on HomeLane. 1000+ Design Experts, 23% Off. Book now!
Ad 2: Book a free online consultation with one of our 1000+ brilliant designers. Get Up to 23% Off on HomeLane.
Ad 3: Does a mix of Art Deco and Minimalism Styles sound good? Explore Interiors on HomeLane!
Ad 4: Explore Modular Style Interior Designs. Austere Elegance and High-Quality Material. Only on HomeLane.

###
Example 3
Brand: {self.input_dict['bu_detail']}
Article:
{self.input_dict['reference_description']}
Interest Keyword: "{self.input_dict['interest_keyword']}"
Write 10 Descriptions for the Brand, Article, and Interest given above. Include Brand Name in each Ad.
Ad 1:'''
            }]

        self.nlg_parameters = {
            'n' : math.ceil(self.input_dict['n_generations']) + 2,
            'response_length': 400,
            'temperature': 0.9,
            'top_p': 1,
            'frequency_penalty': 0.6,
            'presence_penalty': 1
        }

        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)
        return

    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations_list = [] 

        for generation in self.nlg_generations_list:
            generation = 'Ad 1:' + generation
            t_gens = generation.split('\n')
            t_gens = [':'.join(el.split(':')[1:]).strip() for el in t_gens]
            if t_gens:
                self.extracted_generations_list.extend(t_gens)
        return 
    
    @Lever.log_postprocess
    def postprocess(self) -> None:
        post_process_obj = self.postprocess_class(title_case=False, ending_exclusions='!#', exclude_domain=True, exclude_phone_number=True)
        # TODO: + pass inputs to self.postprocess_class
        #       - fix long sentences
        #       - remove incomplete sentences
        #       - make domain lowercase

        self.post_process_list = []
        for generation in self.extracted_generations_list:
            self.post_process_list.append(post_process_obj.run(generation, input_dict=self.input_dict))
        self.post_process_list = [el.replace("_", "") for el in self.post_process_list]
        return

    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        filter_pipeline_obj = self.filter_generations_class(
            min_length=60, 
            max_length=90)
        self.filter_generations_list, self.filtered_generations = filter_pipeline_obj.run(
            self.post_process_list, 
            self.input_dict['reference_description'],
            input_dict=self.input_dict)
        # Selecting the first word from bu_details as brand_name
        brand_name = self.input_dict['bu_detail'].split()[0].replace("_", "").lower()
        # Filtering only gens which contain brand_name
        # self.filter_generations_list = [el for el in self.filter_generations_list if brand_name in el.lower()]
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
                'generic': self.performance_generations_dict_list[:no_of_outputs]
            }
            return self.filter_generations_list, self.log_json
        except Exception as exc:
            _, _, exc_traceback = sys.exc_info()
            trace = traceback.format_tb(exc_traceback)
            updated_log_json = {"trace": trace, "exception":str(exc), "info": self.log_json}
            return {"generic":[]}, updated_log_json

if __name__ == '__main__':
    # TODO: add prompt temptlate, params, support dict to csv for google

    pp = {
        'engine': 'text-davinci-002',
        'response_length': 1050,
        'temperature': 0.85,
        'top_p': 1,
        'frequency_penalty': 0.6,
        'presence_penalty': 1,
        'stop_seq': ["###"]
    }
    sd = {}

    id = {
        "bu_detail": "Livspace is an interior design startup that offers a platform that connects people to designers, services, and products",
        "reference_description": "1. Understand the strong and weak points of your product even at the prototyping stage.\n2. Want to know what your users think about your product, website or mobile app?",
        "interest_keyword": "Userbrain",
        "bu_name": "Interior Design",
        "n_generations": 10
    }

    # print(gens)
    # print(len(gens['generic']))
