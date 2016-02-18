from __future__ import print_function

str_search_list = ['veght', 'vegheight']
replace_str = "vh"

mod_name1 = 'veght45122a3'


for found_str in str_search_list:
    mod_name1 = mod_name1.replace(found_str, replace_str)
    

for found_str in str_search_list:
    if set(mod_name1) & set(found_str):
        print(found_str)
        mod_name1 = mod_name1.replace(found_str, replace_str)


if any(found_str in mod_name1 for found_str in str_search_list):
    print(found_str)
    mod_name1 = mod_name1.replace(found_str, replace_str)
    print(mod_name1) 

    
for found_str in set(str_search_list).intersection(mod_name1.split()):
    print(found_str)
    mod_name1 = mod_name1.replace(found_str, replace_str)
    print(mod_name1) 