from ds.lever import Lever

class FacebookThemes(Lever):

    @Lever.log_generate
    def generate(self) -> None:
        self.prompt = [
            {
                "role": "system", 
                "content": "You are a helpful digital marketing assistant for identifying themes for the given Brand and Ad Copy"},

            {
                "role": "user", 
                "content": f'''Identify themes for the given Brand and Ad Copy.
###
Example 1
Brand: PharmEasy is one of India’s leading healthcare aggregators and most trusted medicine delivery app. PharmEasy helps patients connect with local pharmacy stores and diagnostic centers in order to fulfill their extensive medical needs.
Ad Copy:
1: Still not sure where to get your Gall Stone Removed? Check how our customers are swearing by PharmEasy SurgiCare. Ensure the best treatment experience customised to your needs. Contact us now & get FREE Doctor Consultation
2: Permanent Lipoma Removal Surgery! Avail a painless procedure with PharmEasy SurgiCare. Scarless and Painless. FREE doctor consultation. 100% cashless procedures. Additional PharmEasy Benefits. Contact Us Now!
3: Get your Cataract treated in a Day. Check out what our Customers are saying. PharmEasy SurgiCare ensure a Hassle-Free treatment process for you.
4: The solution for your Gall bladder pain is here. Connect with the expert doctors and get premium care with the help of PharmEasy SurgiCare. Discounts on diagnostic tests 100% cashless procedures. Latest technologies. FREE doctor consultation
5: Still not sure where to get your Appendix Surgery? Check how our customers are swearing by PharmEasy SurgiCare. Ensure the best treatment experience customised to your needs.
6: Save Big on Medicines with PharmEasy Today! Get Flat 20% Off and 20% Cashback. Avail Flat 250 Cashback on ICICI Debit & Credit Cards. Use Code - PHEA20. Order Now!
7: Get rid of Hernia in a day. Check out what our Customers have to say. PharmEasy Surgicare takes care of the whole treatment process so that you don't have to worry. Contact us now & get FREE Doctor Consultation
8: Still not sure where to get your Hydrocele Surgery? Check how our customers are swearing by PharmEasy SurgiCare. Ensure the best treatment experience customised to your needs. Contact us now & get FREE Doctor Consultation.
#
Write 10 Themes for the "Ad Copy" given above. Each Theme must be less than 3 words.
#
Theme 1: Free consultation
Theme 2: Best Treatment Experience
Theme 3: PharmEasy SurgiCare
Theme 4: Gallstone treatment
Theme 5: Expert Doctors
Theme 6: Cataract Treatment
Theme 7: Surgery
Theme 8: Medicines
Theme 9: Hernia Treatment
Theme 10: Hydrocele Surgery
###
Example 2
Brand: FloMattress is an online shopping company for sleeping mattresses. It has varieties like Ergo and Ortho. It also offers accessories like Adjustable Pillow(Fibre),  Adjustable Pillow(Memory Foam), waterproof protector and eye masks. It provides a 100-night risk free trial.
Ad Copy:
1: Experience deep sleep with Flo mattress that gives your complete orthopedic support. Get 10 years warranty with 100% refund after 100 nights trial.
2: Say hello to great sleep with Flo. Check out what Gogi Tech, Mumbaiker Nikhil & Dhruv Rathee have to say about their experience with Flo mattress.
3: Buy Flo mattress that is perfectly customized according to your sleeping preferences so that you get deep sleep.
#
Write 5 Themes for the "Ad Copy" given above. Each Theme must be less than 3 words.
#
Theme 1: Orthopedic Support
Theme 2: Free trial
Theme 3: 10 years warranty
Theme 4: 100% refund
Theme 5: Deep Sleep
###
Example 3
Brand: {self.input_dict['bu_detail']}
Ad Copy:
{self.input_dict['brand_ads']}
#
Write 10 Themes for the "Ad Copy" given above.
#
Theme 1:'''
            }]

        self.nlg_parameters = {
            'response_length': 256,
            'temperature': 0.8,
            'top_p': 1,
            'frequency_penalty': 0,
            'presence_penalty': 1,
            "n": 3
        }

        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, self.nlg_parameters)
        
    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations = []
        for generation in self.nlg_generations_list:
            generation = '1:' + generation
            t_gens = generation.split('\n')
            t_gens = [':'.join(el.split(':')[1:]).strip() for el in t_gens]
            if t_gens:
                self.extracted_generations.extend(t_gens)
       
    @Lever.log_postprocess
    def postprocess(self) -> None:
        post_process_obj = self.postprocess_class(title_case=True, exclude_exclamation=True)
        self.post_process_list = []
        for generation in self.extracted_generations:
            self.post_process_list.append(post_process_obj.run(generation))

    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        pass

    def run(self, input_dict):
        self.input_dict = input_dict
        self.generate()
        self.extract_label()
        self.postprocess()
        self.filter_generations()
        return self.post_process_list
   
if __name__ == '__main__':
    pass
# ad_account_id = 2904992326
# ad_group_id = 63963090431
# generations, input_headlines, input_descriptions = generate(ad_account_id, ad_group_id)
