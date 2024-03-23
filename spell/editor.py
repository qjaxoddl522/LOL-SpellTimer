import os
import glob
from PIL import Image

#현재 디렉터리의 모든 이미지 파일 가져오기
image_files = glob.glob(os.path.join(os.getcwd(), '*.[pjJ][npP][gG]'))

for image_file in image_files:
    image = Image.open(image_file)

    black = Image.new('RGBA', image.size, (0, 0, 0, 128)) #50% 투명도의 검은색

    #원본 이미지와 합성
    result = Image.alpha_composite(image.convert('RGBA'), black)

    #결과 이미지 저장
    result.save(os.path.basename(image_file).split('.')[0]+'CT.png') #이름만 가져오기
