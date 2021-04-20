---
noteId: "42e2fab055e711ebb405ff67790a3315"
tags: []

---

# FY2020 Quick Search Analysis

## GC Document Processing to JSON required before hand


```python
import json
import pandas as pd
with open('NDAA_FY2020.json') as f:
  data = json.load(f)
```

## Defining Keywords for analysis
Current keywords: transform, reform

Choosing stem words to catch the largest amount of variance



```python
keywords = ['transform', 'reform']
key_dict = {}
```


```python
for par in data['paragraphs']:
    for key in keywords:
        if key in par['par_raw_text_t']:
            if key in key_dict:
                key_dict[key].append(par)
            else:
                key_dict[key] = [par]
```


```python
all_df = []
out_dict = []
for keyword in keywords:
    for item in key_dict[keyword]:
        entity = []
        for ent in item['entities']:
            for ent_s in item['entities'][ent]:
                entity.append(ent_s)
        out_dict.append({
            'keyword': keyword,
            'filename':item['filename'],
            'page_num':item['page_num_i'],
            'par_raw_text_t':item['par_raw_text_t'],
            'entities':entity,
        })
df = pd.DataFrame(out_dict)
df
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>keyword</th>
      <th>filename</th>
      <th>page_num</th>
      <th>par_raw_text_t</th>
      <th>entities</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>transform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>110</td>
      <td>H . R . 6395—111 ( d )AGENCY PARTICIPATION.—Th...</td>
      <td>[the Food and Drug Administration, the Nationa...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>transform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>353</td>
      <td>H . R . 6395—354 and applicability of such tec...</td>
      <td>[the Chief Information Office, the Defense Adv...</td>
    </tr>
    <tr>
      <th>2</th>
      <td>transform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>551</td>
      <td>H . R . 6395—552 ‘ ‘ ( vi ) transformation of ...</td>
      <td>[State, the Department of Defense, SEC, C the ...</td>
    </tr>
    <tr>
      <th>3</th>
      <td>transform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>657</td>
      <td>H . R . 6395—658 ( B ) notify the appropriate ...</td>
      <td>[National Security Space Launch, the Space For...</td>
    </tr>
    <tr>
      <th>4</th>
      <td>transform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>1065</td>
      <td>H . R . 6395—1066 SEC . 4201 .RESEARCH , DEVEL...</td>
      <td>[T&amp;E, RAND ARROYO CENTER, MLRS, CHINOOK, SEC, ...</td>
    </tr>
    <tr>
      <th>5</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>2</td>
      <td>H . R . 6395—3 Sec . 212 .Disclosure requireme...</td>
      <td>[the Joint Artificial Intelligence Center, the...</td>
    </tr>
    <tr>
      <th>6</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>10</td>
      <td>H . R . 6395—11 Sec . 757 .Study on force mix ...</td>
      <td>[Department of Defense, Department of Veterans...</td>
    </tr>
    <tr>
      <th>7</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>11</td>
      <td>H . R . 6395—12 Sec . 838 .Comptroller General...</td>
      <td>[Congress, the Small Business Technology Trans...</td>
    </tr>
    <tr>
      <th>8</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>23</td>
      <td>H . R . 6395—24 Sec . 2503 .Execution of proje...</td>
      <td>[Department of Defense, Department of Defense ...</td>
    </tr>
    <tr>
      <th>9</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>66</td>
      <td>H . R . 6395—67 Sec . 212 .Disclosure requirem...</td>
      <td>[the Joint Artificial Intelligence Center, the...</td>
    </tr>
    <tr>
      <th>10</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>96</td>
      <td>H . R . 6395—97 Defense as the Secretary consi...</td>
      <td>[the Joint Artificial Intelligence Center, D Q...</td>
    </tr>
    <tr>
      <th>11</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>334</td>
      <td>H . R . 6395—335 ( 4 )The effect of any such l...</td>
      <td>[the Federal Government, nent, United States C...</td>
    </tr>
    <tr>
      <th>12</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>340</td>
      <td>H . R . 6395—341 ( 3 )The increase , as compar...</td>
      <td>[Department of Defense, the Joint Artificial I...</td>
    </tr>
    <tr>
      <th>13</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>341</td>
      <td>H . R . 6395—342 Sec . 832 .Extension of pilot...</td>
      <td>[Department of Defense, the Small Business Tec...</td>
    </tr>
    <tr>
      <th>14</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>359</td>
      <td>H . R . 6395—360 ( 5 )SECRETARY CONCERNED.—The...</td>
      <td>[the Department of Defense, SEC, United States...</td>
    </tr>
    <tr>
      <th>15</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>373</td>
      <td>H . R . 6395—374 SEC . 838 .COMPTROLLER GENERA...</td>
      <td>[the Defense Science Board Task Force, the Dep...</td>
    </tr>
    <tr>
      <th>16</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>412</td>
      <td>H . R . 6395—413 an analysis of the process us...</td>
      <td>[Congress, Subtitle BOther Department of Defen...</td>
    </tr>
    <tr>
      <th>17</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>413</td>
      <td>H . R . 6395—414 of the Department of Defense ...</td>
      <td>[Congress, the Department of Defense, SUBMITTA...</td>
    </tr>
    <tr>
      <th>18</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>414</td>
      <td>H . R . 6395—415 General of the United States ...</td>
      <td>[Department of Defense, the Department of Defe...</td>
    </tr>
    <tr>
      <th>19</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>543</td>
      <td>H . R . 6395—544 ‘ ‘ ( 1 ) A staffing plan to ...</td>
      <td>[Congress, Hizballah, Islamic Revolutionary Gu...</td>
    </tr>
    <tr>
      <th>20</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>551</td>
      <td>H . R . 6395—552 ‘ ‘ ( vi ) transformation of ...</td>
      <td>[State, the Department of Defense, SEC, C the ...</td>
    </tr>
    <tr>
      <th>21</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>553</td>
      <td>H . R . 6395—554 ( D ) an assessment of the ex...</td>
      <td>[Congress, State, air force, the Committee on ...</td>
    </tr>
    <tr>
      <th>22</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>568</td>
      <td>H . R . 6395—569 ( 6 ) affirms the commitment ...</td>
      <td>[State, Congress, the Department of Defense, S...</td>
    </tr>
    <tr>
      <th>23</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>580</td>
      <td>H . R . 6395—581 ( C )1 member selected by agr...</td>
      <td>[TRANSITIONAL PERIOD.The, the General Intellig...</td>
    </tr>
    <tr>
      <th>24</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>581</td>
      <td>H . R . 6395—582 intelligence services and str...</td>
      <td>[SEC, the Child Soldiers Prevention Act, Congr...</td>
    </tr>
    <tr>
      <th>25</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>587</td>
      <td>H . R . 6395—588 of title 10 , United States C...</td>
      <td>[Department of Defense, United Nations, SEC, t...</td>
    </tr>
    <tr>
      <th>26</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>589</td>
      <td>H . R . 6395—590 involved in the illicit trade...</td>
      <td>[State, SEC, Fed, FORM.The, Cabinet, the Sover...</td>
    </tr>
    <tr>
      <th>27</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>928</td>
      <td>H . R . 6395—929 Subtitle B—Military Family Ho...</td>
      <td>[Department of Defense, Guam Realignment, Neva...</td>
    </tr>
    <tr>
      <th>28</th>
      <td>reform</td>
      <td>NDAA_FY2020.pdf</td>
      <td>1112</td>
      <td>H . R . 6395—1113 SEC . 4501 .OTHER AUTHORIZAT...</td>
      <td>[PROC REPLACEMENT &amp; MODERNIZATION, OFFICE OF T...</td>
    </tr>
  </tbody>
</table>
</div>



## Writing simple table to file
Output File is in attached CSV at
NDAA_FY2020_QuickSearch.csv


```python
df.to_csv('NDAA_FY2020_QuickSearch.csv')
```

## Further Analysis


```python

```


```python

```
