import math
import sys
import traceback

from ds.lever import Lever


import logging


class HeadlineGenericKeyword(Lever):

    @Lever.log_generate
    def generate(self) -> None:
        self.prompt = [
            {
                "role": "user", 
                "content": f'''Rephrase the given Reference Copy to generate creative Google ad Headlines for the given Brand, Reference Copy, and Interest.
#
Example 1

Brand: CoverWallet makes it easy for businesses to understand, buy and manage insurance. All online, in minutes. We make it simple, convenient, and fast for you to get the coverage you need at the right price. 
Reference Copy: Insurance for business. On-demand liability insurance. 100% Online, In Minutes.
Interest: "insurance against cyber crime"
Write 7 Headlines for the Brand, Reference Copy, and Interest given above. Each Headline must be less than 6 words. Use Context from Interest.
#

1: Quick and Paperless Insurance
2: Instant policies, no paperwork
3: Protection against Hackers
4: Defend Your Business from Leaks
5: Insurance tailored to your needs
6: Don't lose sleep over Hackers!
7: Protection Against Data Spill
###
Example 2

Brand: HomeLane is a home interior company that helps homeowners do their home interiors in a personalized and pocket-friendly way. Explore thousands of inspiring interior designs or get a free estimate.
Reference Copy: Modern Home Interior Designs. Unbeatable Quality & 23% Off. Customize your Dream Home
Interest: "trendy modular kitchens interiors 2020"
Write 9 Headlines for the Brand, Reference Copy, and Interest given above. Each Headline must be less than 6 words. Use Context from Interest.
#

1: Unmatched Quality at 23% Off
2: Design Your Dream Cookery
3: Personalized and affordable
4: Your dream home on a budget!
6: 1000+ Flawless Interior Designs
7: Kitchen Makeover in a Snap
8: Homeowners, get your free quote!
9: Create Your Dream Kitchen Today
###
Example 3

Brand: {self.input_dict['bu_detail']}
Reference Copy: {self.input_dict['reference_headline']}
Interest: "{self.input_dict['interest_keyword']}"
Write 10 Headlines for the Brand, Reference Copy, and Interest given above. Each Headline must be less than 6 words. Use Context from Interest.
#

1:'''
            }]

        self.nlg_parameters = {
            'n' : 3,
            'response_length': 256,
            'temperature': 0.85,
            'top_p': 1,
            'frequency_penalty': 0.4,
            'presence_penalty': 1
        }
        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)

    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations_list = [] 
        for generation in self.nlg_generations_list:
            generation = 'Questions:' + generation
            t_gens = generation.split('\n')
            t_gens = [':'.join(el.split(':')[1:]).strip() for el in t_gens]
            self.extracted_generations_list.extend(t_gens)

    @Lever.log_postprocess
    def postprocess(self) -> None:
        post_process_obj = self.postprocess_class(title_case=True, ending_exclusions='.!', exclude_domain=True, exclude_phone_number=True)
        # TODO: + pass inputs to self.postprocess_class
        #       + article fix
        #       + incorrect offer
        #       + preserve unusual capitalization from inputs
        
        self.post_process_list = []
        for generation in self.extracted_generations_list:
            self.post_process_list.append(post_process_obj.run(generation, input_dict=self.input_dict))
        self.log_json['self.postprocess_class_labels'] = self.post_process_list  


    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        self.extracted_generations_list = [el for el in self.extracted_generations_list if self.input_dict['bu_name'].lower() not in el.lower()]
        filter_pipeline_obj = self.filter_generations_class(
            min_length=self.min_length, 
            max_length=30)
        # TODO: Add ISF filter
        self.filter_generations_list, self.filtered_generations = filter_pipeline_obj.run(
            self.post_process_list, 
            self.input_dict['reference_headline'],
            input_dict=self.input_dict)
        self.log_json['filtered_generations'] = self.filter_generations_list

        score_performance_obj = self.score_performance_class(brand_name=self.input_dict['bu_name'])
        self.performance_list = score_performance_obj.get_performance_scores(generations_list=self.filter_generations_list)
        cluster_text_obj = self.cluster_text_class(threshold=80)
        self.performance_generations_dict_list, self.log_json['discarded_low_performance_generations'] = cluster_text_obj.get_unique_assets_by_filter_key(input_assets=self.performance_list)
        return 

    
    @Lever.log_run       
    def run(self, input_dict):
        try:
            self.input_dict = input_dict
            logging.debug("Google headline_generic_kw generate started")
            no_of_outputs = self.input_dict['n_generations']
            self.input_dict['n_generations'] *= 0.1
            self.input_dict['n_generations'] = math.ceil(self.input_dict['n_generations']) + 2

            self.generate()
            self.extract_label()
            self.postprocess()
            self.filter_generations()
            # TODO: - while loop to keep generating
            #       - content filtering

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

    pt= '''Rephrase the given Reference Copy to generate creative Google ad Headlines for the given Brand, Reference Copy, and Interest.
#
Example 1

Brand: CoverWallet makes it easy for businesses to understand, buy and manage insurance. All online, in minutes. We make it simple, convenient, and fast for you to get the coverage you need at the right price. 
Reference Copy: Insurance for business. On-demand liability insurance. 100% Online, In Minutes.
Interest: "Cyber"
#
Write 7 Headlines for the Brand, Reference Copy, and Interest given above. Each Headline must be less than 6 words. Use Context from Interest.
#

1: Quick and Paperless Insurance
2: Instant policies, no paperwork
3: Protection against Hackers
4: Defend Your Business from Leaks
5: Insurance tailored to your needs
6: Don't lose sleep over Hackers!
7: Protection Against Data Spill
###
Example 2

Brand: HomeLane is a home interior company that helps homeowners do their home interiors in a personalized and pocket-friendly way. Explore thousands of inspiring interior designs or get a free estimate.
Reference Copy: Modern Home Interior Designs. Unbeatable Quality & 23% Off. Customize your Dream Home
Interest: "Modular Kitchen"
#
Write 9 Headlines for the Brand, Reference Copy, and Interest given above. Each Headline must be less than 6 words. Use Context from Interest.
#

1: Unmatched Quality at 23% Off
2: Design Your Dream Cookery
3: Personalized and affordable
4: Your dream home on a budget!
6: 1000+ Flawless Interior Designs
7: Kitchen Makeover in a Snap
8: Homeowners, get your free quote!
9: Create Your Dream Kitchen Today
###
Example 3

Brand: {self.input_dict['bu_detail']}
Reference Copy: {reference_headline}
Interest: "{self.input_dict['interest_keyword']}"
#
Write 10 Headlines for the Brand, Reference Copy, and Interest given above. Each Headline must be less than 6 words. Use Context from Interest.
#

1:'''


    pp = {
        'engine': 'text-davinci-002',
        'response_length': 100,
        'temperature': 0.85,
        'top_p': 1,
        'frequency_penalty': 0.4,
        'presence_penalty': 0,
        'stop_seq' : ["###"]
    }
    sd = {}

    id = {
        "bu_detail": "Swiggy delivers yummy food to your doorsteps.",
        "reference_headline": "Get tasty food at best prices. Delivered in 20 mins. Choose from 500+ restaurants. $20 Off",
        "interest_keyword": "Pizza",
        "bu_name": "Swiggy",
        "benefit_used": "Gluten free",
        "n_generations": 10
    }

    # gens, rej_gens = HeadlineGeneric(prompt_templete=pt, self.nlg_parameters=pp, support_dict=sd).run(input_dict=id)
    # print(gens)
    # print(len(gens['generic']))
    # print(pt.format(**id))

    # t_p = self.postprocess_class(title_case=False, ending_exclusions='.!', exclude_domain=True, exclude_phone_number=True)
    # print(t_p.run('Get an Pizza" Delivered. thesis is best. $55 Off on Swiggy', id))
