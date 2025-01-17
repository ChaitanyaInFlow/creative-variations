
import re
import sys
import traceback

from threading import Thread

from ds.process.cluster_text import ClusterText

# from ds.levers.uac.uac_extended_theme import UACExtendedThemeGeneration
from ds.levers.theme.extended_themes_brand import ExtendedThemeBrandGeneration
from ds.levers.uac.uac_extended_theme_from_serp import UACExtendedThemeFromSerpGeneration

from ds.process.serp_data_pipeline import get_text_data_from_serp
from ds.scripts.detect_industry import DetectIndustry

import logging



class ThreadWithReturnValue(Thread):
    
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args,
                                                **self._kwargs)
    def join(self, *args):
        Thread.join(self, *args)
        return self._return

def get_extended_themes_from_serp(brand_name, brand_detail, theme=''):
    industry = DetectIndustry().get_industry(brand_name)
    search_query = f'{industry} {theme}'.strip()
    serp_data, _ = get_text_data_from_serp(search_query)
    
    serp_data = '\n'.join(['- '+el for el in serp_data])

    generations, _ = UACExtendedThemeFromSerpGeneration().run({
            "brand_detail": brand_detail,
            "theme": theme,
            "serp_data": serp_data
        })
    
    output_dict_list = []
    for theme in generations:
        if theme:
            output_dict_list.append({'text':theme})
    return output_dict_list

def get_extended_themes(brand_name, brand_detail, theme=''):
    logs_dict = {}
    serp_thread = ThreadWithReturnValue(target=get_extended_themes_from_serp, args=(brand_name, brand_detail, theme,))
    serp_thread.start()
    gpt_extended_themes, _ = ExtendedThemeBrandGeneration().run({
            "brand_detail": brand_detail,
            "theme": theme
        })
    serp_extended_themes = serp_thread.join()

    extended_themes = gpt_extended_themes + serp_extended_themes
    logs_dict['more_themes'] = extended_themes

    #filter_obj = self.filter_generations_class(max_length=60, threshold=80)
    unique_extended_themes, _ = ClusterText(threshold=86).get_unique_sentences(extended_themes)
    logs_dict['filtered_extended_themes'] = unique_extended_themes

    return unique_extended_themes, logs_dict

def main_extended_themes(theme, brand_name, brand_detail):
    ''' Where themes is one theme from the list of themes, for which we want to get extended themes.'''
    '''theme should be a string, not list'''

    logs_dict = {}

    logs_dict['theme'] = theme
    logs_dict['brand_name'] = brand_name
    logs_dict['brand_detail'] = brand_detail

    try:

        more_themes, logs = get_extended_themes(brand_name, brand_detail, theme)
        logs_dict['more_themes'] = logs['more_themes']
        logs_dict['filtered_extended_themes'] = logs['filtered_extended_themes']


        return more_themes, logs_dict

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        trace = traceback.format_tb(exc_traceback)
        updated_log_json = {"trace": trace,
                            "exception": str(exc), "info": logs_dict}
        return [], updated_log_json

if __name__ == '__main__':
    # themes = ['Natural Lipstick', 'LipBalm']
    # theme = "Shoe"
    brand_name = 'LifeStyle'
    brand_detail = "WESTSIDE is a lead fashion brand with over 22 labels all designed in-house, across women\\u2019s wear, menswear, kids wear, footwear, lingerie, cosmetic, perfumes, accessories and home furniture."
    theme =  "Artificial Intelligence In Advertising"
    extended_themes_result, logs_dict = main_extended_themes(
        theme, brand_name, brand_detail)

    print('\nExtended Themes:', extended_themes_result)
    print('\nlogs_dict:', logs_dict)

    # brand_detail = "Mamaearth products are made using safe, pure, gentle, natural, and toxin-free ingredients.They provide various products for beauty, skin, hair, and baby care needs."
    # brand_name = "Mamaearth"
    # theme = "Running Shoes"


    # serp_data, serp_theme = get_extended_themes_from_serp(brand_name, brand_detail, theme)

    # print('\n### BRAND NAME: ', brand_name)
    # print('\n### THEME: ', theme)
    # print('\n### SERP DATA:\n', serp_data)
    # print('\n### SERP THEME:\n', serp_theme)

