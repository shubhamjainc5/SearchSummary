from sentence_transformers import CrossEncoder
import time
import pandas as pd
import logging
Logger = logging.getLogger(__name__)
import traceback
from typing import List, Dict
import copy

rerank_model = CrossEncoder('cross-encoder/ms-marco-TinyBERT-L-2')


async def rerank_documents(response_text: List[Dict[str, str]], query: str) -> (List[Dict[str, str]], str):
    print('\n---------Document encoder reranking-------------\n')
    
    try:
        rerank_text = copy.deepcopy(response_text)
        start_time = time.time()
        model_inputs = [[query, passage['content']] for passage in rerank_text]
        rr_scores = rerank_model.predict(model_inputs)
        print("score calculation took {:.4f} seconds".format(time.time() - start_time))

        start_time = time.time()
        for i in range(len(rr_scores)):
            rerank_text[i]['rerank_score']=round(float(rr_scores[i]), 4)
        print("score assignment took {:.4f} seconds".format(time.time() - start_time))

        start_time = time.time()
        rerank_text = sorted(rerank_text, key=lambda k: k['rerank_score'], reverse=True)
        print("document sorting took {:.4f} seconds".format(time.time() - start_time))
        result_status = 'SUCCESS'
    except Exception as e:
        Logger.error(traceback.format_exc())
        Logger.error('ERROR: DOCUMENT RERANKING FAILED')
        rerank_text = response_text
        result_status = 'ReRank Failed'

    return rerank_text, result_status


# query = 'how to remove hard water stains?'
# rs = requests.post('http://3.111.180.30:6000/haystack',json= {"query":query,"top_k":10},
#                    headers={"Content-Type": "application/json"})

# response_text = json.loads(rs.text)

# response_text = [{'content': '• Fill drain traps with water. • Deep clean to remove stains inside toilet bowls and around the base of urinals. ', 'meta': {'Ind_number': 491, 'bbox': '[ 71.335014 641.73157  437.30954  669.56757 ]', 'file_name': 'Guidelines-for-Green-Cleaning-May-2009', 'image_caption': '', 'image_name': 'Guidelines-for-Green-Cleaning-May-2009_page10_list_tensor(0.9661)3.png', 'image_text': '', 'image_type': 'list', 'keywords_document': 'Cleaning,GREEN CLEANING POLICY,Contents GREEN CLEANING,Office Cleaning Safety,Cleaning Related Training,Cleaning Products,Green Cleaning,Green Cleaning Products,Safety Office Cleaning,Green Cleaning Program', 'keywords_page': 'dry cleaning tasks,cleaning tasks performed,cleaning,cleaning tasks,Clean,surfaces,restroom cleaning,Remove,wet,Clean restrooms', 'meta_author': '', 'meta_creationDate': '2009-06-01 10:10:32', 'meta_creator': 'Adobe Acrobat Pro 9.1.1', 'meta_encryption': '', 'meta_format': 'PDF 1.6', 'meta_keywords': '', 'meta_modDate': '2009-06-01 10:14:00', 'meta_producer': 'Adobe Acrobat Pro 9.1.1', 'meta_subject': '', 'meta_title': '', 'meta_trapped': '', 'page_num': 'page10', 'type': 'list'}, 'score': 0.8807639813401166}, {'content': 'An acid is often used to remove hard-water deposits, discoloration on metal surfaces and rust stains.  White vinegar and lemon juice are mild acids that can be used in place of commercial products.  Lemon juice should not be used on silver. Prolonged exposure to an acid may irritate the respiratory tract, so it is important to provide adequate ventilation when using the products. ', 'meta': {'Ind_number': 3033, 'bbox': '[ 38.825535 645.2488   300.06293  738.7649  ]', 'file_name': 'Cleaning_Healthy__Green_HACE-E-73-2', 'image_caption': '', 'image_name': '', 'image_text': '', 'image_type': 'text', 'keywords_document': 'cleaning products,products,cleaning,cleaning product,product,reduce,clean,place,cleaning product needed,dust', 'keywords_page': 'soaps and detergents,products,cleaning,Surfactants,Bleach,cleaning products,surfaces,sodium,remove,alkali', 'meta_author': '', 'meta_creationDate': '2009-04-03 14:18:52', 'meta_creator': 'Adobe InDesign CS4 (6.0.1)', 'meta_encryption': '', 'meta_format': 'PDF 1.7', 'meta_keywords': '', 'meta_modDate': '2009-04-03 14:18:57', 'meta_producer': 'Adobe PDF Library 9.0', 'meta_subject': '', 'meta_title': '', 'meta_trapped': '', 'page_num': 'page0', 'type': 'text'}, 'score': 0.8485253112784926}, {'content': 'Bathroom Disinfectants are similar to general disinfectants, but typically may have an acidic pH (closer to 1) to remove hard water deposits in sinks, bowls and urinals. The selection issues include both those under general disinfectants and bathroom cleaners. Care in selection and use is important. The following are some of the specific issues to compare for this product category: ', 'meta': {'Ind_number': 1916, 'bbox': '[ 71.92688 506.63446 542.69653 561.14575]', 'file_name': 'git_green_cleaning_manual', 'image_caption': '', 'image_name': '', 'image_text': '', 'image_type': 'text', 'keywords_document': 'Cleaning Products,Slightly Satisfied Satisfied,Dissatisfied Dissatisfied Slightly,Dissatisfied Slightly Dissatisfied,GREEN CLEANING,CLEANING,green cleaning program,Neutral Slightly Satisfied,Slightly Dissatisfied Neutral,Dissatisfied Neutral Slightly', 'keywords_page': 'Preferable Ingredients,Preferable Active Ingredients,bathroom cleaners,Prefer,ingredients,compared,Preferable,Bathroom,cleaners,Prefer antimicrobial ingredients', 'meta_author': 'Mary Margaret Murphy', 'meta_creationDate': '2013-12-17 17:19:42', 'meta_creator': 'Microsoft® Word 2010', 'meta_encryption': '', 'meta_format': 'PDF 1.6', 'meta_keywords': '', 'meta_modDate': '2013-12-17 17:21:14', 'meta_producer': 'Microsoft® Word 2010', 'meta_subject': '', 'meta_title': '', 'meta_trapped': '', 'page_num': 'page8', 'type': 'text'}, 'score': 0.7749064772420327}, {'content': '• Similar to baking soda (not for use in cooking)• Odorless• Stain remover – has alkaline properties• Water softener - treats hard water• Descale coffee machines or  bathroom tiles', 'meta': {'Ind_number': 1683, 'bbox': '[ 40.435284 371.93185  179.55621  510.90408 ]', 'file_name': 'green-cleaning-recipe-guide', 'image_caption': '', 'image_name': 'green-cleaning-recipe-guide_page5_list_tensor(0.9400)2.png', 'image_text': '', 'image_type': 'list', 'keywords_document': 'Environmental Protection Agency,Protection Agency,baking soda,White vinegar,cup white vinegar,water,soda,products,Washing soda,vinegar', 'keywords_page': 'Stain remover,baking soda,Stain,Fabric softener,soda,washing soda,remover,bleach,Lime deposit remover,Water', 'meta_author': '', 'meta_creationDate': '2023-02-23 13:19:36', 'meta_creator': 'Adobe InDesign 18.1 (Macintosh)', 'meta_encryption': '', 'meta_format': 'PDF 1.4', 'meta_keywords': '', 'meta_modDate': '2023-02-23 13:19:50', 'meta_producer': 'Adobe PDF Library 17.0', 'meta_subject': '', 'meta_title': '', 'meta_trapped': '', 'page_num': 'page5', 'type': 'list'}, 'score': 0.7713368996765283}, {'content': 'Bleaches are used to remove stains and disinfect surfaces.  Chlorine bleach, commonly referred to as household bleach, contains sodium hypochlorite and may cause severe damage or irritation to eyes, skin and respiratory system.  Avoid breathing the vapors.  Alternatives to chlorine bleach are oxygen or non-chlorine bleaches, which usually contain hydrogen peroxide, sodium perborate or sodium percarbonate.  ', 'meta': {'Ind_number': 3029, 'bbox': '[311.83868 321.79666 573.2732  450.7725 ]', 'file_name': 'Cleaning_Healthy__Green_HACE-E-73-2', 'image_caption': '', 'image_name': '', 'image_text': '', 'image_type': 'text', 'keywords_document': 'cleaning products,products,cleaning,cleaning product,product,reduce,clean,place,cleaning product needed,dust', 'keywords_page': 'soaps and detergents,products,cleaning,Surfactants,Bleach,cleaning products,surfaces,sodium,remove,alkali', 'meta_author': '', 'meta_creationDate': '2009-04-03 14:18:52', 'meta_creator': 'Adobe InDesign CS4 (6.0.1)', 'meta_encryption': '', 'meta_format': 'PDF 1.7', 'meta_keywords': '', 'meta_modDate': '2009-04-03 14:18:57', 'meta_producer': 'Adobe PDF Library 9.0', 'meta_subject': '', 'meta_title': '', 'meta_trapped': '', 'page_num': 'page0', 'type': 'text'}, 'score': 0.7604718227835607}, {'content': 'The word green is often used to market products and services. There are no government definitions of the word green. There aren’t laws for how the word can be used. This makes it hard for the consumer. ', 'meta': {'Ind_number': 3192, 'bbox': '[ 66.19441 257.1257  289.9751  324.4286 ]', 'file_name': 'FactSheet_WhatIsGreen', 'image_caption': '', 'image_name': '', 'image_text': '', 'image_type': 'text', 'keywords_document': 'Environment Safer Disinfectants,safer,products,safer products,infectious disease,Green,cleaning,Green cleaning,people,disinfectants', 'keywords_page': 'safer,products,Environment Safer Disinfectants,safer products,cleaning,environment,disinfectants,Green,cleaning products,Safer Disinfectants', 'meta_author': '', 'meta_creationDate': '2021-04-29 15:25:49', 'meta_creator': 'Adobe InDesign 16.1 (Macintosh)', 'meta_encryption': '', 'meta_format': 'PDF 1.7', 'meta_keywords': '', 'meta_modDate': '2021-04-29 15:29:43', 'meta_producer': 'Adobe PDF Library 15.0', 'meta_subject': '', 'meta_title': '', 'meta_trapped': '', 'page_num': 'page0', 'type': 'text'}, 'score': 0.7421437359431078}, {'content': '• Vinegar is a proven natural cleaner, disinfectant, and deodorizer.• Lemon juice works to dissolve soap residue and hard water deposits.• Baking soda can be used as an abrasive cleaner to scrub surfaces or as a deodorizer.', 'meta': {'Ind_number': 126, 'bbox': '[395.88135 846.1918  563.64795 905.17303]', 'file_name': 'green-cleaning-undated', 'image_caption': '', 'image_name': 'green-cleaning-undated_page1_list_tensor(0.8792)5.png', 'image_text': '', 'image_type': 'list', 'keywords_document': 'National Park Service,green cleaning,cleaning,National Park,cleaning products,products,national parks,Park,Cleaning National Parks,Yellowstone National Park', 'keywords_page': 'National Park Service,National Park,products,cleaning,cleaning products,green cleaning,National parks,Yellowstone National Park,Park,Cleaning National Parks', 'meta_author': '', 'meta_creationDate': '2006-07-10 00:00:00', 'meta_creator': 'Adobe InDesign CS (3.0.1)', 'meta_encryption': '', 'meta_format': 'PDF 1.4', 'meta_keywords': '', 'meta_modDate': '2007-01-05 14:31:17', 'meta_producer': 'Adobe PDF Library 6.0', 'meta_subject': '', 'meta_title': 'Cleaning.indd', 'meta_trapped': '', 'page_num': 'page1', 'type': 'list'}, 'score': 0.7364482305358869}, {'content': '      The university will establish standard operating procedures to address how an effective cleaning, hard floor, and carpet maintenance system will be consistently utilized, managed and audited. This will specifically address cleaning to protect vulnerable occupants, such as occupants with asthma, other respiratory conditions, or sensitive or damaged skin. ', 'meta': {'Ind_number': 1505, 'bbox': '[ 71.66059 631.2007  530.26697 681.13477]', 'file_name': 'green-cleaning-policy', 'image_caption': '', 'image_name': '', 'image_text': '', 'image_type': 'text', 'keywords_document': 'Green Cleaning Program,cleaning products,advance social responsibility,cleaning,Green Cleaning,Social Responsibility,Green Cleaning Policy,Sustainable Cleaning Products,meet Green Seal,Sustainable Cleaning Equipment', 'keywords_page': 'impact air quality,adversely impact air,public entry points,Employing permanent entryway,particulates entering buildings,dirt and potentially,capture dirt,dirt and particulates,potentially hazardous chemical,Employing permanent', 'meta_author': '', 'meta_creationDate': '2016-12-22 14:04:50', 'meta_creator': 'Microsoft® Word 2016', 'meta_encryption': '', 'meta_format': 'PDF 1.5', 'meta_keywords': '', 'meta_modDate': '2020-03-27 11:58:21', 'meta_producer': 'Microsoft® Word 2016', 'meta_subject': '', 'meta_title': 'Green Cleaning Policy', 'meta_trapped': '', 'page_num': 'page4', 'type': 'text'}, 'score': 0.7304744375009478}, {'content': 'Green Cleaning Toolkit for Early Care and Education 50 Cleaning • Uses a detergent and water to physically remove dirt, grime and germs from surfaces. This process does not necessarily kill germs.  • Removes molds and allergens that can trigger asthma symptoms.    Has been found to remove as much as  99% of  germs when microfiber cleaning tools are used.  50 ', 'meta': {'Ind_number': 2372, 'bbox': '[2.9624990e-01 6.2826008e-01 7.2000000e+02 5.3274927e+02]', 'file_name': 'green_cleaning', 'image_caption': 'a diagram of the different types of bacteria', 'image_name': 'green_cleaning_page49_figure_tensor(0.9856)1.png', 'image_text': "[['Green Cleaning Toolkit for Early Care and Education'], ['Cleaning', '• Uses a detergent and water to physically remove dirt , grime and germs from surfaces . This process does not necessarily kill germs . • Removes molds and allergens that can trigger asthma symptoms .'], ['Has been found to remove as much as 99 % of germs when microfiber cleaning tools are used .'], ['50']]", 'image_type': 'image', 'keywords_document': 'Green Cleaning Toolkit,Early Care,Cleaning Toolkit,Green Cleaning,Toolkit for Early,Care and Education,North Carolina South,Carolina South Carolina,North Dakota South,Dakota South Dakota', 'keywords_page': 'Green Cleaning Toolkit,Care and Education,Toolkit for Early,Early Care,physically remove dirt,Cleaning Toolkit,detergent and water,water to physically,Green Cleaning,Education', 'meta_author': 'Victoria', 'meta_creationDate': '2013-11-14 15:07:36', 'meta_creator': 'Acrobat PDFMaker 9.0 for PowerPoint', 'meta_encryption': '', 'meta_format': 'PDF 1.5', 'meta_keywords': '', 'meta_modDate': '2013-11-14 15:09:47', 'meta_producer': 'Adobe PDF Library 9.0', 'meta_subject': '', 'meta_title': 'Green Cleaning, Sanitizing and Disinfection: A Toolkit for Early Care and Education', 'meta_trapped': '', 'page_num': 'page49', 'type': 'figure'}, 'score': 0.7288861591664118}, {'content': '• Gently scrape up solids with a spoon or bone scraper, working from the outside of the spot toward the center to prevent spreading. • Blot the spotted area with a dry white towel or paper towels. Continue blotting the area by pressing firmly with a clean portion of the toweling until there is no further transfer from the spot. Then begin use of spot remover chemicals. NOTE: Do not scrub stains. Scrubbing action can damage the fabric and spread the stain. Use blotting action. • Never soak upholstery. Over-wetting with cleaning solution or water will make effective cleaning difficult. Messy spills will spread, and soiled water will seep deep into the fabric, cushions and wood frame. • Test for color fastness: Never pour cleaning solution directly on a spot or spill. Put solution on a white towel and in an inconspicuous area, apply with a blotting action to the upholstery before attempting to remove the spot. If color from the fabric transfers to the towel, do not attempt to remove the spot. Call a professional cleaner for help. • Finding the color to be fast, continue blotting with the spotting solution as above. ', 'meta': {'Ind_number': 476, 'bbox': '[ 71.90801 533.19226 558.2984  715.2647 ]', 'file_name': 'Guidelines-for-Green-Cleaning-May-2009', 'image_caption': '', 'image_name': 'Guidelines-for-Green-Cleaning-May-2009_page9_list_tensor(0.9931)2.png', 'image_text': '', 'image_type': 'list', 'keywords_document': 'Cleaning,GREEN CLEANING POLICY,Contents GREEN CLEANING,Office Cleaning Safety,Cleaning Related Training,Cleaning Products,Green Cleaning,Green Cleaning Products,Safety Office Cleaning,Green Cleaning Program', 'keywords_page': 'Pick up litter,carpet,cleaning,spot,carpet cleaning,cleaning solution,solution,Pick,Vacuum carpet,Spot Cleaning Carpets', 'meta_author': '', 'meta_creationDate': '2009-06-01 10:10:32', 'meta_creator': 'Adobe Acrobat Pro 9.1.1', 'meta_encryption': '', 'meta_format': 'PDF 1.6', 'meta_keywords': '', 'meta_modDate': '2009-06-01 10:14:00', 'meta_producer': 'Adobe Acrobat Pro 9.1.1', 'meta_subject': '', 'meta_title': '', 'meta_trapped': '', 'page_num': 'page9', 'type': 'list'}, 'score': 0.7253308772688595}]

# model = CrossEncoder('cross-encoder/ms-marco-TinyBERT-L-2')

# start_time = time.time()
# model_inputs = [[query, passage['content']] for passage in response_text]
# rr_scores = model.predict(model_inputs)
# print("score calculation took {:.4f} seconds".format(time.time() - start_time))

# start_time = time.time()
# for i in range(len(rr_scores)):
#      response_text[i]['score']=rr_scores[i]
# print("score assignment took {:.4f} seconds".format(time.time() - start_time))

# start_time = time.time()
# response_text = sorted(response_text, key=lambda k: k['score'], reverse=True)
# print("document sorting took {:.4f} seconds".format(time.time() - start_time))
# print('--')



# passages = [ t['content']  for t in response_text]
# prev_scores = [ t['score']  for t in response_text]

# model = CrossEncoder('cross-encoder/ms-marco-TinyBERT-L-2')

# start_time = time.time()

# #Concatenate the query and all passages and predict the scores for the pairs [query, passage]
# model_inputs = [[query, passage] for passage in passages]
# scores = model.predict(model_inputs)

# #Sort the scores in decreasing order
# results = [{'input': inp, 'score': score} for inp, score in zip(model_inputs, scores)]
# rerank_scores = [ r['score'] for r in results]
# results = sorted(results, key=lambda x: x['score'], reverse=True)

# print("Query:", query)
# print("Search took {:.2f} seconds".format(time.time() - start_time))
# for hit in results[0:5]:
#     print("Score: {:.2f}".format(hit['score']), "\t", hit['input'][1])

# print(pd.DataFrame(zip(passages,prev_scores,rerank_scores), columns=['passages','prev_scores','rerank_scores']))
# print('--')