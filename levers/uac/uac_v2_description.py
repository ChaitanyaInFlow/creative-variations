#Import our own files

from ds.lever import Lever

import logging


class UACDescriptionGeneration(Lever):


    @Lever.log_generate
    def generate(self) -> None:
        self.prompt = [
            {
                "role": "system", 
                "content": f'''
Write creative Google ad Headlines for the given Brand and Themes. 

###
Generation 1

Brand: Rapido is India's first and fastest-growing Bike taxi app with a whopping 25 Million+ app downloads. Rapido bike taxi provides the best intra-city commuting services and is currently operating in 100+ cities. It is considered as the most affordable choice.

Themes: Shopping, Comfort , Affordable

Write 6 Headlines based on the Themes for the given Brand. Each Headline must be less than 18 words.

Headline 1: Affordable autos for your daily commuting and shopping needs.
Headline 2: Going to the mall with family? Rapido auto can take you there safely and affordably!
Headline 3: Tired of being stuck in traffic? Let Rapido auto take you to your destination comfortably!
Headline 4: No more standing in queues for an auto. Book Rapido autos from the comfort of your home!.
Headline 5: Commute burning a hole in your wallet? Not anymore! Use Rapido Auto for lowest fare.
Headline 6: No more high-fares, get pocket-friendly auto-rides

###
Generation 2

Brand: Swiggy is an online food ordering and delivery platform. It helps users order food from their favorite restaurants near them and track their delivery partner.

Themes: Swiggy, 50% Off, Cricket Season

Write 6 Headlines based on the Themes for the given Brand. Each Headline must be less than 18 words.

Headline 1: Pick From a Wide Selection Of Restaurants With Amazing Discounts. Order Now On Swiggy.
Headline 2: Watch The Cricket Season With Swiggy! Enjoy 50% Off Your First Order. 
Headline 3: Score A Half-Price Meal This Cricket Season With Swiggy’s 50% Discount Offer.
Headline 4: Watch The Match With Swiggy! Get 50% Off On Your First Order.
Headline 5: Score Swiggy’s Cricket Season Deal. Get 50% Off. Order Online Now!
Headline 6: Use Swiggy’s Top Deal and Get 50% Off this Cricket Season! Order Now.

###
Generation 3

Brand: {self.input_dict['bu_detail']}

Themes: {self.input_dict['input_themes']}

Write 6 Headlines based on the Themes for the given Brand. Each Headline must be less than 18 words.

Headline 1:'''
            }]

        self.nlg_parameters = {
            "response_length": 500,
            "temperature": 0.77,
            "top_p": 1,
            "frequency_penalty": 1,
            "presence_penalty": 1,
            "stop_seq": "[]",
            "n" : 3
        }

        self.nlg_generations_list, _ = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)

    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations = []
        for generation in self.nlg_generations_list:
            generation_list = generation.split('\n')
            for i in range(len(generation_list)):
                generation_list[i] = generation_list[i].replace('Headline ' + str(i+1) + ':', '')
            self.extracted_generations += generation_list
       
    @Lever.log_postprocess
    def postprocess(self) -> None:
        post_process_obj = self.postprocess_class(title_case=False, exclude_exclamation=False)
        self.post_process_list = []
        for generation in self.extracted_generations:
            self.post_process_list.append(post_process_obj.run(generation, self.input_dict))

    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        filter_obj = self.filter_generations_class(
            max_length=90, 
            min_length=30,
            threshold=80)
        self.filtered_list, rejected_list= filter_obj.run(
            self.post_process_list, 
            reference_ad='',
            input_dict=self.input_dict)  # Need to add reference ad logic

    @Lever.log_run       
    def run(self, input_dict):
        self.input_dict = input_dict
        self.generate()
        self.extract_label()
        self.postprocess()
        self.filter_generations()

        return self.filtered_list, []

