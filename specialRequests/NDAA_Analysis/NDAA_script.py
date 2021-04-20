import json

with open('NDAA_FY2020.json') as f:
  data = json.load(f)

print(data['id'])

for item in data:
    print(item)

count_transform = 0
for par in data['paragraphs']:
    #print(par['id'] + ' - \n'+ par['par_raw_text_t']+ "\n\n")
    if "transformation" in par['par_raw_text_t']:
        count_transform += 1
        print(par['id'] + ' - \n'+ par['par_raw_text_t']+ "\n\n")

print("Transformation: "+ str(count_transform))
        

