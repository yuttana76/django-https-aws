class const:

# Remove const
    def getStatusTxt(compCode, statusCode):
        res = ""
        try:
            if "waitApprove" == statusCode:
                res = "ระหว่างพิจารณา"
            elif "onprocess" == statusCode:
                res = "ระหว่างดำเนินการ"
            elif "approve" == statusCode:
                res = "ระหว่างดำเนินการ"
            elif "finish" == statusCode:
                res = "เรียบร้อย"
            elif "reject" == statusCode:
                res = "ปฏิเสธ"
            elif "success" == statusCode:
                res = "ดำเนินการสำเร็จ"
            elif "fail" == statusCode:
                res = "ดำเนินการไม่สำเร็จ"
            else:
                res = "Not assign"

            return res

        except Exception as e:
            return res

    def maskingTxt(text):
        text1 = text[:int(len(text)/2)] + "****"
        return text1
