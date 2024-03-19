# coding=utf8
import hashlib
import cv2
import ddddocr
from PIL import Image
import pytesseract
import requests
from bs4 import BeautifulSoup
import os
from sklearn.svm import SVC
from sklearn.externals import joblib
import numpy as np

url = 'http://nw-restriction.nttdocomo.co.jp/'
url1 = 'top.php'
url2 = 'search.php'
url3 = 'result.php'

def filehash(file_name):
    # 读取文件
    with open(file_name, 'rb') as fp:
        data = fp.read()
    # 使用 md5 算法
    file_md5 = hashlib.md5(data).hexdigest()
    return file_md5

def download_gif(session):

    response = session.get(url + url2)
    soup = BeautifulSoup(response.content, 'html.parser')
    node1 = soup.find('img', src="gifcat/call.php")
    if node1:
        response = session.get(url + 'gifcat/call.php')
        imgPath = "./source_img/call.gif"
        with open(imgPath, 'wb') as f:
            f.write(response.content)
            f.close()
        filename = gif_png(imgPath)
        return filename
    else:
        return 'error1'

def verifycode(imei, session, code):
    product = imei
    post_url =url + url2
    #headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'}
    data={
        'productno':product,
        'attestationkey':code
    }
    data_response = session.post(url=post_url, data=data)
    #data_response = session.get(url+url3)
    # data_status = data_response.status_code
    # data_html = data_response.text
    # #print(data_status)
    # print(data_html)
    soup=BeautifulSoup(data_response.content, 'html.parser')
    #print(soup)
    node = soup.find('span',
                         style='width:250px; display:inline-block; font-size: 3em; padding: 4px; border: 2px solid #CC0033;')
    if node:
        return node.text
    else:
        return "error2"

def gif_png(gifFileName):
    im = Image.open(gifFileName)
    try:
        while True:
            current = im.tell()
            im.seek(current + 1)
    except EOFError:
        fp = './test_img/' + str(current) + '.png'
        im.save(fp)
        hashstr = filehash(fp)
        newfp = './test_img/' + str(current) + '_' + hashstr + '.png'
        os.rename(fp, newfp)
        pass
    filename = str(current) + '_' + hashstr + '.png'
    return filename

def ocrImg(fileName):
    clf = joblib.load('number.pkl')
    p = Image.open('test_img/%s' % fileName)
    b_img = binarizing(p, 170)
    imgs=cut_image(b_img)
    captcha = []
    for i, img in enumerate(imgs):
        path = 'test_img/code_%s.png' % i
        img.save(path)
        data = getletter(path)
        data = np.array([data])
        # print(data)
        oneLetter = clf.predict(data)[0]
        # print(oneLetter)
        captcha.append(oneLetter)
    captcha = [str(i) for i in captcha]
    print("the captcha is :%s" % ("".join(captcha)))
    return "".join(captcha)

def binarizing(img, threshold):
    """传入image对象进行灰度、二值处理"""
    img = img.convert("L")  # 转灰度
    pixdata = img.load()
    w, h = img.size
    # 遍历所有像素，大于阈值的为黑色
    for y in range(h):
        for x in range(w):
            if pixdata[x, y] < threshold:
                pixdata[x, y] = 0
            else:
                pixdata[x, y] = 255
    # img.save('temp/0.png')
    return img


def cut_image(img):
    imgs = []
    w, h = img.size
    if w==150:
        cut = [(0, 0, 30, h), (30, 0, 60, h), (60, 0, 90, h), (90, 0, 120, h), (120, 0, w, h)]
    elif w==180:
        cut = [(0, 0, 30, h), (30, 0, 60, h), (60, 0, 90, h), (90, 0, 120, h), (120, 0, 150, h), (150, 0, w, h)]
    for i, n in enumerate(cut, 1):
        temp = img.crop(n)
        imgs.append(temp)
        #temp.save("temp/cut_%s.png" % i)
    return imgs

def ocrImgAndSave(fileName, imgs):
    for i, cur_img in enumerate(imgs):
        # 设置tesseract的工作目录
        #pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract'
        #recNum = pytesseract.image_to_string(cur_img, config='-psm 7 outputbase letters')
        ocr = ddddocr.DdddOcr()
        recNum = ocr.classification(cur_img)
        print(recNum)
        for r in replaceArray:
            recNum = recNum.replace(r, replaceArray[r]).lower()
        if (recNum.isdigit() and len(recNum) == 1):
            # recNum = pytesseract.image_to_string(cur_img, config='-psm 10 outputbase digits')
            recdString = fileName + "-" + str(i + 1) + ".png"
            path = 'temp/' + recNum + "/"
            if not os.path.exists(path):
                os.mkdir(path)
            imgPath = path + recdString
            cur_img.save(imgPath)
        else:
            recdString = fileName + "-" + str(i + 1) + ".png"
            path = 'temp/'
            if not os.path.exists(path):
                os.mkdir(path)
            imgPath = path + recdString
            cur_img.save(imgPath)

def extractLetters(path):
    x = []
    y = []
    # 遍历文件夹 获取下面的目录
    for root, sub_dirs, files in os.walk(path):
        for dirs in sub_dirs:
            # 获得每个文件夹的图片
            for fileName in os.listdir(path + '/' + dirs):
                print(fileName)
                # 打开图片
                x.append(getletter(path + '/' + dirs + '/' + fileName))
                y.append(dirs)

    return x, y

def getletter(fn):
    fnimg = cv2.imread(fn)  # 读取图像
    img = cv2.resize(fnimg, (8, 8))  # 将图像大小调整为8*8
    alltz = []
    for now_h in range(0, 8):
        xtz = []
        for now_w in range(0, 8):
            b = img[now_h, now_w, 0]
            g = img[now_h, now_w, 1]
            r = img[now_h, now_w, 2]
            btz = 255 - b
            gtz = 255 - g
            rtz = 255 - r
            if btz > 0 or gtz > 0 or rtz > 0:
                nowtz = 1
            else:
                nowtz = 0
            xtz.append(nowtz)
        alltz += xtz
    return alltz

def run_project(times,imei,session):
    times = times+1
    if times == 3:
        return 1
    result = download_gif(session)
    if result == 'error1':
        print(str(times) + ' : ' + result)
        print('Fail to download gif!')
        run_project(times,imei,session)

    filename = result
    code = '11111'  # ocrImg(filename)
    if times == 2:
        code = ocrImg(filename)

    result = verifycode(imei, session, code)
    if result == 'error2':
        print(str(times) + ' : ' + result)
        print('Fail to verify code!')
        run_project(times, imei, session)
    else:
        print(result)
    return 0

def doVerify(imei,session):

    result = download_gif(session)
    if result == 'error1':
        print('Fail to download gif!')
        return result

    filename = result
    code = ocrImg(filename)

    result = verifycode(imei, session, code)
    if result == 'error2':
        print('Fail to verify code!')

    return result

if __name__ == '__main__':
    replaceArray = {'o': '0', 'c': '0', 's': '5'}
    #gif_png('./source_img/call0.gif')
    if not os.path.exists('source_img'):
        os.mkdir('source_img')
    if not os.path.exists('gif_to_png'):
        os.mkdir('gif_to_png')
    if not os.path.exists('test_img'):
        os.mkdir('test_img')
    # array = extractLetters('temp')
    # # 使用向量机SVM进行机器学习
    # letterSVM = SVC(kernel="linear", C=1).fit(array[0], array[1])
    # # 生成训练结果
    # joblib.dump(letterSVM, 'number.pkl')
    # for root, sub_dirs, files in os.walk('gif_to_png'):
    #     for file in files:
    #         print('发现图片:' + file)
    #         p = Image.open('gif_to_png/%s' % file)
    #         b_img = binarizing(p, 170)
    #         imgs=cut_image(b_img)
    #         ocrImgAndSave(file, imgs)
    session = requests.Session()
    response = session.get(url + url1)
    soup = BeautifulSoup(response.content, 'html.parser')
    node = soup.find('a', href='search.php')
    imei = '356596051659016'
    # times = 0
    # if node:
    #     result = run_project(times, imei, session)
    #     exit(result)
    # else:
    #     exit(1)

    maxretry = 3
    for i in range(maxretry):
        result = doVerify(imei, session)
        if result == 'error1' or result == 'error2':
            continue
        else:
            print(result)
            exit(0)
    exit(1)

    # soup = BeautifulSoup(response.content, 'html.parser')
    # node = soup.find('a', href='search.php')
    # if node:
    #     response = session.get(url + url2)
    #     download_gif(response)

