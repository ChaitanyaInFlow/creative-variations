import requests
import json
import os

# from ds.scripts.detect_industry import DetectIndustry 

def brand_api_industry(brand_name):
	if brand_name == '':
		return 'Others'
	try:
		url = f"{os.getenv('GSEARCH_AI_URL')}generation/generic/brand?brand_name={brand_name}"
		payload = ""
		headers = {
			'x-api-key': os.getenv('GSEARCH_AI_KEY')
		}
		print(url, headers)
		response = requests.request("GET", url, headers=headers, data=payload)
		return json.loads(response.text).get('brand_details')[0]['industry']
	except:
		# return DetectIndustry().get_perf_industry(brand_name)
		return 'Others'

if __name__ == '__main__':
   
   brand_name_1 = 'smartasset' # okbrand
   brand_name_2 = 'Suri' # ok
   brand_name_3 = '' # ok

   industry = brand_api_industry('brand_name_1')
   print("### ", industry) 