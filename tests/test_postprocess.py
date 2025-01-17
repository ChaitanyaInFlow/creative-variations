import sys
import pytest


import re
from titlecase import titlecase        
from ds.process.postprocess import PostProcess

from nltk import tokenize


def test_postprocess():
    test_set_long = [
        (
            '''free Learn how easy it is to Roll Over your Traditional ira to a Roth ira. get started today irA!
it's time to Roll Over your retirement accounts, capitalize can help you do it for free free!''',
            '''Free learn how easy it is to roll over your traditional IRA to a roth IRA. Get started today IRA. 
It's time to roll over your retirement accounts, Capitalize can help you do it for Free Free.'''
        ),
        (
            '''tired of managing multiple retirement accounts? let us help you roll them over into one.
looking To Make The Switch From Traditional IRA to Roth IRA? we can help you Roll Over!''',
            '''Tired of managing multiple retirement accounts? Let us help you roll them over into one. 
Looking to make the switch from traditional IRA to roth IRA? We can help you roll over.'''
        ),
        (
            '''Tax-Free growth and withdrawals? sounds too good to be true, but we can make it happen.''',
            '''Tax-free growth and withdrawals? Sounds too good to be true, but we can make it happen.'''
        )
    ]


    post_process_obj = PostProcess(title_case=False, ending_exclusions='#', exclude_domain=True, exclude_phone_number=True)
    for test_case, truth in test_set_long:
        output = post_process_obj.run(test_case, input_dict={'bu_name': 'Capitalize', 'interest_keyword': 'Free IRA'}, preserve_capital_keys=['interest_keyword', 'bu_name'])
        print('test_case:' + test_case)
        print('output:' + output)
        print('truth :'+ truth)

        assert output == truth

    
    test_set_short = [
        (
            '''Get best deals on Amazon.com , words largest store!''',
            '''Get Best Deals On Amazon.com, Words Largest Store.'''
        )
    ]

    for test_case, truth in test_set_short:
        post_process_obj = PostProcess(title_case=True, ending_exclusions='#', exclude_exclamation=True)
        output = post_process_obj.run(test_case)
        print('test_case:' + test_case)
        print('output:' + output)
        print('truth :'+ truth)

        assert output == truth



def test_junkchar():
    test_set = [
        (
            '''##THIS IS a test string that ends with junk chars!#''',
            '''THIS IS a test string that ends with junk chars'''
        )
    ]

    for test_case, truth in test_set:
        post_process_obj = PostProcess(title_case=False, ending_exclusions='#!', exclude_exclamation=False)
        output = post_process_obj.remove_junk_characters(test_case)
        print('test_case:' + test_case)
        print('output:' + output)
        print('truth :'+ truth)

        assert output == truth

def test_capital():
    test_set_sentence = [
        (
            '''this is a sentence. consider it has wrong capitalization!\nlets see if its fixed''',
            '''This is a sentence. Consider it has wrong capitalization!\nLets see if its fixed'''
        ),
        (
            'Lets see what happes with domain.com names. in sentences ofcorse',
            'Lets see what happes with domain.com names. In sentences ofcorse',
        ),
    ]

    test_set_title = [
        (
            'This is a headline. easy-to-read!',
            'This Is A Headline. Easy-To-Read!'
        ),
        (
            'buy on amazon.com',
            'Buy On Amazon.com'
        ),
    ]


    for test_case, truth in test_set_sentence:
        post_process_obj = PostProcess(title_case=False, ending_exclusions='#', exclude_domain=True, exclude_phone_number=True)
        output = post_process_obj.process_capitalisation(test_case)
        print('test_case:' + test_case)
        print('output:' + output)
        print('truth :'+ truth)

        assert output == truth

    for test_case, truth in test_set_title:
        post_process_obj = PostProcess(title_case=True, ending_exclusions='#', exclude_exclamation=True)
        output = post_process_obj.process_capitalisation(test_case)
        print('test_case:' + test_case)
        print('output:' + output)
        print('truth :'+ truth)

        assert output == truth

def test_punctuation():
    test_set = [
        (
            '''Can we get ,the correct punctuations ..for this string ?''',
            '''Can we get, the correct punctuations. for this string?'''
        ),
        (
            'All these , pauses never ,felt right to me...',
            'All these, pauses never, felt right to me.'
        ),
        (
            'What if i add domain.com names to the mix ?',
            'What if i add domain.com names to the mix?'
        ),
        (
            'There -are no-changes to- hyphens - ',
            'There -are no-changes to- hyphens -'
        )
    ]

    for test_case, truth in test_set:
        post_process_obj = PostProcess(title_case=False, ending_exclusions='#', exclude_exclamation=False)
        output = post_process_obj.process_puntuation(test_case)
        print('test_case:' + test_case)
        print('output:' + output)
        print('truth :'+ truth)

        assert output == truth

def test_articlefix():
        test_set = [
            (
                '''This is an great day to be out for a hour.''',
                '''This is a great day to be out for an hour.'''
            ),
            (
                'This is an tale of an unicorn and an yetti.',
                'This is a tale of a unicorn and a yetti.'
            )
        ]

        for test_case, truth in test_set:
            post_process_obj = PostProcess(title_case=False, ending_exclusions='#', exclude_domain=True, exclude_phone_number=True)
            output = post_process_obj.run(test_case)
            print('test_case:' + test_case)
            print('output:' + output)
            print('truth :'+ truth)

            assert output == truth


def test_fixtargetword():
    test_set = [
        (
            '''free Learn how easy it is to Roll Over your Traditional ira to a Roth ira. get started today irA!
it's time to Roll Over your retirement accounts, capitalize can help you do it for free free!''',
            '''Free Learn how easy it is to Roll Over your Traditional IRA to a Roth IRA. get started today IRA!
it's time to Roll Over your retirement accounts, capitalize can help you do it for Free Free!'''
        ),
        (
            'Get the info about ira and use get50off to get 50% off on your ira.',
            'Get the info about IRA and use GET50OFF to get 50% off on your IRA.'
        ),
        (
            ' free ira comaprision and 50% off using coupon code get50off',
            'Free IRA comaprision and 50% off using coupon code GET50OFF'
        )
    ]

    for test_case, truth in test_set:
        post_process_obj = PostProcess(title_case=False, ending_exclusions='#', exclude_domain=True, exclude_phone_number=True)
        output = post_process_obj.fix_target_word('Free IRA GET50OFF', test_case)
        
        print('test_case:' + test_case)
        print('output:' + output)
        print('truth :'+ truth)

        assert output == truth


def test_fix_titlecase():
    test_set = [
        (
            '''get expert help with ira''',
            '''Get Expert Help With Ira'''
        ),
        (
            'Free & easy IRA comparison',
            'Free & Easy IRA Comparison'
        ),
        (
            'find the right iRA now',
            'Find The Right iRA Now'
        ),
        (
            "compare and transfer ira",
            "Compare And Transfer Ira"
        ),
        (
            "compare ira with Ease",
            "Compare Ira With Ease"
        ),
        (
            "best IRA Options, now!",
            "Best IRA Options, Now!"
        )
    ]
    for test_case, truth in test_set:
        post_process_obj = PostProcess(title_case=True, ending_exclusions='#', exclude_domain=True, exclude_phone_number=True)
        output = post_process_obj.process_capitalisation(test_case)
        print('test_case:' + test_case)
        print('output:' + output)
        print('truth:', truth)
        print()
        assert output == truth


def test_fix_brand_name():
    test_set = [
        [(
            '''Get smart with smart asset''',
            '''Get smart with SmartAsset'''
        ),
        (
            'smart asset is smart',
            'SmartAsset is smart'
        ),
        (
            'Buy asset insurance on Smart asset',
            'Buy asset insurance on SmartAsset'
        )],
        [(
            "Get comfortable with all Birds",
            "Get comfortable with AllBirds"
        ),
        (
            "all birds is for all",
            "AllBirds is for all"
        ),
        (
            "Get all birds shoes",
            "Get AllBirds shoes"
        )],
        [(
            "Order groceries on swiggy instamart",
            "Order groceries on Swiggy Instamart"
        )
        ],
        [(
            "Find the right insurance with smart asset inc.",
            "Find the right insurance with SmartAsset Inc."
        ),
        (
            "want an insurance. contact smartasset inc",
            "want an insurance. contact SmartAsset Inc"
        )]
    ]

    brand_names = ['SmartAsset', 'AllBirds', 'Swiggy Instamart', 'SmartAsset Inc']

    for index, test_cases in enumerate(test_set):
        for test_case, truth in test_cases:
            brand_name = brand_names[index]
            post_process_obj = PostProcess(title_case=True, ending_exclusions='#', exclude_domain=True, exclude_phone_number=True)
            output = post_process_obj.fix_brand_name(brand_name, test_case)
            print('test_case:', test_case)
            print('output:', output)
            print('truth:', truth)
            print()
            assert output == truth


def test_remove_unclosed_quotes():
    test_set = [
    (
        '''Get Expert Help With "ira"''',
        '''Get Expert Help With "ira"'''
    ),
    (
        'Free & Easy ira" comparison',
        'Free & Easy ira comparison'
    ),
    (
        '"Find The Right Ira Now',
        'Find The Right Ira Now'
    ),
    (
        '''compare "And" "Transfer ira''',
        '''compare "And" Transfer ira'''
    )]

    for test_case, truth in test_set:
        post_process_obj = PostProcess(title_case=True, ending_exclusions='#', exclude_domain=True, exclude_phone_number=True)
        output = post_process_obj.remove_unclosed_quote(test_case)
        
        print('test_case:', test_case)
        print('output:', output)
        print('truth :', truth)
        print()

        assert output == truth


def test_pipeline():


    test_set = [
        (
            '''Get Expert Help With ira''',
            '''Get Expert Help With Ira'''
        ),
        (
            'Free & Easy ira comparison',
            'Free & Easy Ira Comparison'
        ),
        (
            'Find The Right Ira Now',
            'Find The Right Ira Now'
        ),
        (
            "compare And Transfer ira",
            "Compare And Transfer Ira"
        ),
        (
            "Get Started With A New ira",
            "Get Started With A New Ira"
        ),
        (
            "compare ira With Ease",
            "Compare Ira With Ease"
        ),
        (
            "find the best ira on smart asset",
            "Find The Best Ira On SmartAsset"
        ),
        (
            "Get smart ira with smart Asset",
            "Get Smart Ira With SmartAsset"
        ),
        (
            "Buy iphone on smart asset", 
            "Buy iPhone On SmartAsset"
        ),
        (
            "Buy Iphone on smart asset", 
            "Buy iPhone On SmartAsset"
        
        ),
        (
            '''Find the best IRA on "Smart Asset''',
            '''Find The Best IRA On SmartAsset'''
        )
    ]

    input_dict = {
        "bu_name": "SmartAsset",
        "reference_headline": "Issues with your 401k account? SmartAsset experts can help. Fast, Easy & Completely Free.",
        "interest_keyword": "iPhone",
        "brand_name": "SmartAsset",
        "benefit_used": "",
        "n_generations": 10
    }

    for test_case, truth in test_set:
        post_process_obj = PostProcess(title_case=True, ending_exclusions='#', exclude_domain=True, exclude_phone_number=True)
        output = post_process_obj.run(test_case, input_dict = input_dict)
        
        print('test_case:', test_case)
        print('output:', output)
        print('truth :', truth)
        print()

        assert output == truth


def test_pt():
    test_set = [
        (
            '''simplify online shopping with India's leading e-commerce platform – flipkart.''',
            '''Simplify online shopping with India's leading e-commerce platform – Flipkart.'''
        )]
    
    input_dict = {
        "bu_name": "Flipkart",
        "reference_headline": "Issues with your 401k account? SmartAsset experts can help. Fast, Easy & Completely Free.",
        "interest_keyword": "iPhone",
        "brand_name": "Flipkart",
        "benefit_used": "",
        "n_generations": 10
    }


    for test_case, truth in test_set:
        post_process_obj = PostProcess(title_case=False, exclude_exclamation=False, ending_exclusions='')
        output = post_process_obj.run(test_case, input_dict)
        
        print('test_case:' + test_case)
        print('output:' + output)
        print('truth :'+ truth)

        assert output == truth

    
if __name__ == "__main__":
    test_pipeline()
    # test_fix_brand_name()
    # test_fix_titlecase()
    # test_pt()
    # test_remove_unclosed_quotes()