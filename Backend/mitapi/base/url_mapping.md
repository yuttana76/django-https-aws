Login
http://localhost:8000/mit/client/cidmobOtp/ 


# Page  http://localhost:3000/custPortal

GET http://localhost:8000/mit/client/1/gettaxlatest/
NEW http://localhost:8000/api/tk_gettaxlatest/ 


GET http://localhost:8000/suitability/suit/?compCode=MPS&cardNumber=111&custType=IND
NEW http://localhost:8000/api/tk_get_suit/ 


GET http://localhost:8000/mit/masterValue/getPFreportsbycid/?cid=111
NEW http://localhost:8000/api/tk_getPFreportsbycid/ 


GET http://localhost:8000/mit/masterValue/getShowPortReports/?compCode=MPS
NEW http://localhost:8000/api/tk_getShowPortReports/ 


# Page http://localhost:3000/custPortalConsent/

http://localhost:8000/mit/masterValue/cmpSubjectRequest/ 
NEW http://localhost:8000/api/tk_cmpSubjectRequest/ 
            
            
GET http://localhost:8000/mit/client/undefined/ 401 mitClientAction.js:6 
NEW http://localhost:8000/api/clientinfo/ 

# Page http://localhost:3000/custHistoryConsent/
http://localhost:8000/cmp/consents/getconsent/
NEW http://localhost:8000/api/tk_getconsent/ 


# Page http://localhost:3000/custRequestNew/access

const response = await axios_api.post(`/mit/client/${userId}/submitrequest/`, 
NEW http://localhost:8000/api/tk_submitrequest/ 