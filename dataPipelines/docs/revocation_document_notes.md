## Revoked Documents 
Notes on how to find if a document has been repealed or revoked


### US Code Crawler
Link : https://www.govinfo.gov/app/collection/uscode 

When using gov-info.gov link: Searching for repealed documents can be accessed through the search there is a tag "uscdisposition:" 
with possible values repealed, omitted, transferred, abrogated, eliminated, not used, reserved, standard. 
This tag appearing in the metadata of the file in "details", but can also be searched.
In the search bar, search for *"uscdisposition:repealed"* to find the repealed documents.
All repealed documents will have the word "repealed" in th title, however and the disposition can be found in the metadata. 

In downloader: Inside of the PDF there are notes that list if a chapter has been repealed. An example would be 
Title 3 Chapter 3. 

Example of Revoked Document Link: https://www.govinfo.gov/app/details/USCODE-2017-title3/USCODE-2017-title3-chap3

### DOD Issuances Crawler
##### Link : https://www.esd.whs.mil/DD/DoD-Issuances/

DoD Issuances have a column on the table they are scraped from called Exp. Date that denotes when the policy expires. 
Most documents have expiration dates in the future however there are a few that have expired listed, that can denote 
that the policy is no longer current publications. 

Example: DoDI 5210.91 on the https://www.esd.whs.mil/Directives/issuances/dodi/ page


### Executive Orders Crawler
Link : https://www.federalregister.gov/presidential-documents/executive-orders

In the Executive Orders, list out what documents the orders revoke, are revoked by, amend, etc. with a 
link to the associated order. The document will have a "Revoked by:" when the document is revoked but it might be 
important to be able to view all other disposition notes. Specifically on the source page url in the document details 
section, in the EO Notes section. On the year of orders page it can be found in the *row disposition-notes* classes of 
the html as "Revoked by:". 

Example of Revoked Document: https://www.federalregister.gov/documents/2016/08/26/2016-20713/amendment-to-executive-order-13673

### JCS Pubs Crawler
Link : https://www.jcs.mil/library/

Though I could not find an official repeal or revoke terminology, these documents have a "Current As Of" date. This date
seems to imply that the publication was current on that date; however, in my research I could not verify that assumption.

### IC Policies Crawler
Link : https://www.dni.gov/index.php/what-we-do/ic-policies-reports

IC Policies do not mention anywhere if they have revoked policies or directives. 

Note: The only thing that seems related is there is a section for canceled forms that require a CAC to view, but 
from what I can tell there is no association with cancelled or revoked policies.

### Air Force Crawler
www.e-publishing.af.mil

There is no revoked or repealed tag to find if the publication is still current. However, in the publication's 
product index of the Air Force publish website, when clicking on the "Product Title" (not the number) a table comes up 
with extra details on the publication. While there is not a column that states whether or not a publication has been 
revoked, there is a certified current date that can help determine whether or not the publication is current.
 The "Last Action" column can also help with the state of the publication, but there was no tag that explicitly said 
 revoked, repealed, ommitted or anything of the sort.