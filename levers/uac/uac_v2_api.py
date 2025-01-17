
import pandas as pd
import json
import requests
import numpy as np


class AssetApiCalls:
    def __init__(self, ad_account_id: int, ad_group_id: int) -> None:
        self.ad_account_id = ad_account_id
        self.ad_group_id = ad_group_id

    def get_access_token(self):
        "This function is important because unless we refresh the token, it would expire very fast"

        url = "https://www.googleapis.com/oauth2/v3/token"

        payload = json.dumps({
                   })
        headers = {
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        response = json.loads(response.text)
        self.access_token = response['access_token']

    def get_assets(self):
        " ## Function to POST Api call to get the assets "
        url = f"https://googleads.googleapis.com/v12/customers/{self.ad_account_id}/googleAds:search"
        headers = {
            'Content-Type': 'application/json',
            'developer-token': '',
            'login-customer-id': '',
            'Authorization': f'Bearer {self.access_token}'
        }

        payload = json.dumps({
            "query": f"SELECT ad_group_ad_asset_view.ad_group_ad, ad_group_ad_asset_view.asset,ad_group_ad_asset_view.performance_label, ad_group_ad_asset_view.field_type, asset.text_asset.text FROM ad_group_ad_asset_view where ad_group.id ={self.ad_group_id} AND asset.type='TEXT' "
        })

        self.response = requests.request(
            "POST", url, headers=headers, data=payload)

    def response_to_dataframe(self):
        output = self.response.json()
        df = pd.DataFrame(
            columns=['asset_type', 'asset_text', 'performance_label'])

        for i in range(0, len(output['results'])):
            df.loc[i, 'asset_type'] = output['results'][i]['adGroupAdAssetView']['fieldType']
            df.loc[i, 'asset_text'] = output['results'][i]['asset']['textAsset']['text']
            try:
                df.loc[i, 'performance_label'] = output['results'][i]['adGroupAdAssetView']['performanceLabel']
            except:
                df.loc[i, 'performance_label'] = np.nan
                # we only get performance label for the enabled assets, not the deleted assets
        df.dropna(inplace=True)
        self.df = df

    def fetch_assets(self):
        df = self.df
        headlines_df = df[df['asset_type'] == 'HEADLINE']
        descriptions_df = df[df['asset_type'] == 'DESCRIPTION']
        self.headlines = headlines_df['asset_text'].tolist()
        self.descriptions = descriptions_df['asset_text'].tolist()

    def fetch_low_performing_headlines(self):
        "## Funtion to get a list of low performing headlines/descriptions "
        df = self.df
        assets = df[df['asset_type'] == 'HEADLINE']
        low_assets = assets[(assets['performance_label'] != 'GOOD') & (
            assets['performance_label'] != 'BEST')]
        self.low_headlines_list = low_assets['asset_text'].tolist()

    def fetch_low_performing_descriptions(self):
        "## Funtion to get a list of low performing descriptions "
        df = self.df
        assets = df[df['asset_type'] == 'DESCRIPTION']
        low_assets = assets[(assets['performance_label'] != 'GOOD') & (
            assets['performance_label'] != 'BEST')]
        self.low_descriptions_list = low_assets['asset_text'].tolist()

    def execute(self):
        self.get_access_token()
        self.get_assets()
        self.response_to_dataframe()
        self.fetch_assets()
        #   self.fetch_low_performing_headlines()
        #   self.fetch_low_performing_descriptions()

        return self.headlines, self.descriptions
