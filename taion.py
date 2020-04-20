# taion.py
# A simple python script to extract body temperature 
# from lcd on a thermometer.
# This code is based on code in https://github.com/yan9yu/sdr
#
# Copyright (c) 2020, Masami Yamakawa (MONOxIT)
# This software is released under the MIT License.
#   http://opensource.org/licenses/mit-license.php

# 使用するライブラリの取り込み
import cv2
import os
import numpy as np
from PIL import Image, ExifTags
import csv

# 定数の定義
IMAGE_FILE_PATH = 'data'
DIGIT_SIZE = 16

# ７セグメントフォント データセットの読み込み
samples = np.loadtxt('dataset/generalsamples.data', np.float32)
responses = np.loadtxt('dataset/generalresponses.data', np.float32)
responses = responses.reshape((responses.size, 1))

# K近傍法で怠惰学習
model = cv2.ml.KNearest_create()
model.train(samples, cv2.ml.ROW_SAMPLE, responses)

# 入力画像ファイル一覧作成
image_paths = []
for path,dirs,files in os.walk(IMAGE_FILE_PATH):
    if len(files) > 0:
        for file in files:
            image_paths.append(os.path.join(path,file))
print(image_paths)

# 体温データ出力用リスト用意
csv_list = []

print('繰り返し開始')
for (i, image_path) in enumerate(image_paths):
    
    # パスのフォルダ名をnameに保存し名前ラベルとして使う
    name = image_path.split(os.path.sep)[-2]
    print('名前:',end='');print(name)
    print('画像読み込み:',end='');print(image_path)

    # 画像ファイルから撮影日時取得
    img_exif = Image.open(image_path)
    
    exif = { ExifTags.TAGS[k]: v for k, v in img_exif._getexif().items()
             if k in ExifTags.TAGS }
             
    print(exif['DateTimeOriginal'])
    date_time = exif['DateTimeOriginal'].split()
    date_time[0]=date_time[0].replace(':','/')
    
    # 画像ファイル読み込み
    image = cv2.imread(image_path)
    
    # 取り込んだ画像の幅を縦横比を維持して500ピクセルに縮小
    ratio = 500 / image.shape[1]
    resized_image = cv2.resize(image, dsize=None, fx=ratio, fy=ratio)

    # グレースケールに変換
    gray = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)
    
    # ヒストグラムを平坦化
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    
    # ぼかして均一化
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 輪郭だけにする
    edged = cv2.Canny(blurred, 50, 200, 255)
    
    # 輪郭検出
    contours, hierarchy = cv2.findContours(edged, cv2.RETR_TREE,
                                            cv2.CHAIN_APPROX_SIMPLE)
    
    min_w = 500
    # 検出された輪郭の数繰り返してLCD部分検出
    for cnt in contours:
    
        #輪郭の長さを取得
        arc_length = cv2.arcLength(cnt, True)
        
        # レシオ0.02で近似図形を取得
        approx = cv2.approxPolyDP(cnt, 0.02*arc_length, True)

        # 近似図形の頂点が４つ（四角形）なら
        if len(approx) == 4:
        
            # 輪郭の周りを四角い枠で囲った枠の位置（XY座標）と幅と高さを得る
            #[lcd_x, lcd_y, lcd_w, lcd_h] = cv2.boundingRect(cnt)
            box = cv2.boundingRect(cnt)
            [lcd_x, lcd_y, lcd_w, lcd_h] = box

            # 縦横比がLCDのサイズのようであれば ToDo かつ既定エリアサイズ以上なら
            if 2 <= lcd_w / lcd_h <= 3:
                # resized_imageに赤色の四角（LCDの候補）を描画する
                cv2.rectangle(resized_image, (lcd_x, lcd_y),
                              (lcd_x + lcd_w, lcd_y + lcd_h),
                              (0, 0, 255), 1)
                # 最小サイズを記憶
                if lcd_w < min_w:
                    min_w = lcd_w
                    min_box = box

    # LCDのボックス座標とサイズを取得
    [lcd_x, lcd_y, lcd_w, lcd_h] = min_box
    
    # LCDに枠を描画（確認用）
    cv2.rectangle(resized_image, (lcd_x, lcd_y),
                  (lcd_x + lcd_w, lcd_y + lcd_h), (0, 0, 255), 2)

# 近似図形で画像を切り取りlcdに入れる
    lcd = resized_image[lcd_y:lcd_y+lcd_h, lcd_x:lcd_x+lcd_w]
    
    # lcdのサイズを得る
    height, width, channels = lcd.shape[:3]
    
    # lcdをグレースケールに変換
    gray = cv2.cvtColor(lcd, cv2.COLOR_BGR2GRAY)

    # 明るさを、平均64、標準偏差16で正規化
    gray = (gray - np.mean(gray))/np.std(gray)*16+64
    gray = np.clip(gray, 0, 255).astype(np.uint8)
    
    # ぼかして均一化
    blurred = cv2.fastNlMeansDenoising(gray,h=8)
    print(np.mean(gray))
    
    # 画像を二値化（黒と白だけに）し、白黒反転（数値が白抜きに）
    thresh = cv2.adaptiveThreshold(blurred, 255,
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 21, 2)

    # LCDの中（数値部分）を切り取り、黒フレームに貼り付け、輪郭検出しやすくする。
    # ToDo: Make the margins dynamic.
    framed_image = np.full((height,width),0,np.uint8)
    framed_image[8:height-8, 9:width-9] = thresh[8:height-8, 9:width-9]
    
    # 白抜き数値を太くして、７セグの各セグメント間をくっつける
    kernel = np.ones((3,3),np.uint8)
    dilation = cv2.dilate(framed_image,kernel,iterations = 1)

    # 輪郭検出
    contours, hierarchy = cv2.findContours(dilation, cv2.RETR_LIST,
                                           cv2.CHAIN_APPROX_SIMPLE)
    
    # 温度数値を入れるための辞書を用意
    ondo_dict = {}
    
    # 検出した輪郭だけ繰り返して７セグ数字部分検出しながら分類
    for cnt in contours:
    
        # 検出した輪郭の周りを四角で囲った時の枠の位置とサイズを得る
        [x, y, w, h] = cv2.boundingRect(cnt)
 
        cv2.rectangle(resized_image, (lcd_x+x, lcd_y+y),
                      (lcd_x+x+w, lcd_y+y+h), (0, 255, 0), 1)
 
        # 幅や高さを調べて、液晶の中に表示された数値のサイズと考えられるなら
        if w > width / 15 and w < width /4:
            if h > height / 2:
            
                # 四角描画
                cv2.rectangle(resized_image, (lcd_x+x, lcd_y+y),
                              (lcd_x+x+w, lcd_y+y+h), (0, 255, 0), 2)
                
                # 数値部分を切り取り
                roi = thresh[y:y + h, x:x + w]
                
                # 画像を教師データに合わせてリサイズし、１次元配列に変換
                roismall = cv2.resize(roi, (DIGIT_SIZE, DIGIT_SIZE))
                roismall = roismall.reshape((1, DIGIT_SIZE*DIGIT_SIZE))
                roismall = np.float32(roismall)
                
                # K近傍法 K=5で分類
                retval, results, neigh_resp, dists = model.findNearest(roismall, k=5)
                
                # 分類結果（数値）を数値の位置xをキーに辞書へ追加
                ondo_dict[x] = results[0][0]
                string = str(int(ondo_dict[x]))
                
                # 分類結果を描画
                cv2.putText(resized_image, string,
                            (lcd_x+x, lcd_y-2),
                            cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0),2)
                
    # 辞書をキーで（座標xが小さい順、桁が大きい順に）並べ替え
    sorted_ondo = sorted(ondo_dict.items())
    print(sorted_ondo)

    # 辞書内の数値に重みをかけて、体温値を得る
    factor = 10.0
    ondo = 0.0
    for key, value in sorted_ondo:
        ondo += value * factor
        factor = factor / 10.0
    print(ondo)
    
    # csv形式の表の行を作る　name, date, time, ondo
    line = [name]
    line += date_time
    line += [ondo]
    
    # 表に追加
    csv_list.append(line)
    print(csv_list)
    
    # 確認のための画像を表示
    cv2.imshow('detected', resized_image)
    cv2.waitKey(0)

# csvファイルへ書き込み
with open('out.csv','w') as f:
    writer = csv.writer(f)
    writer.writerows(csv_list)

print('完了')
