import uiautomator2 as u2
d = u2.connect('127.0.0.1:7555')

from xml.etree import ElementTree  # 导入ElementTree模块
import xml.etree.ElementTree as ET

import os
import csv
import re
import pandas as pd
from PIL import ImageDraw
from PIL import Image
from lxml import etree

import extcolors


# 获取当前程序包名
def getCurrentPackageName():
    info = d.app_current()
    return info['package']

# 获取当前应用程序的Activity
def getCurrentActivity():
    info = d.app_current()
    return info['activity'].split('.')[-1]

# 美化xml文件
def prettyXml(element, indent, newline, level = 0):  # elemnt 为传进来的 Element 类，参数 indent 用于缩进，newline 用于换行
    if element:  # 判断element是否有子元素
        if element.text == None or element.text.isspace():  # 如果element的text没有内容
            element.text = newline + indent * (level + 1)
        else:
            element.text = newline + indent * (level + 1) + element.text.strip() + newline + indent * (level + 1)
    temp = list(element) # 将elemnt转成list
    for subelement in temp:
        if temp.index(subelement) < (len(temp) - 1):  # 如果不是list的最后一个元素，说明下一个行是同级别元素的起始，缩进应一致
            subelement.tail = newline + indent * (level + 1)
        else:  # 如果是list的最后一个元素， 说明下一行是母元素的结束，缩进应该少一个
            subelement.tail = newline + indent * level
        prettyXml(subelement, indent, newline, level = level + 1) # 对子元素进行递归操作

# 获取UI层次结构转储内容
def getUIHierarchy(Path):
    xml = d.dump_hierarchy(compressed=False, pretty=False)  # d.dump_hierarchy(compressed=True, pretty=True)
    f = open(Path, 'w', encoding='UTF-8')
    f.write(xml)

# 得到PIL.Image格式的图像
def getUIScreenshot(Path):
    image = d.screenshot()  # default format="pillow"
    image.save(Path)  # 目前只支持png 和 jpg格式的图像

# 从 xml 文件的节点 root 开始遍历，获取该节点及其所有子节点，存入列表 result_list
unique_id = 1  # 全局唯一标识，用于标记节点
def nodeTraversal(root, level, result_list):
    global unique_id
    if level != 0:
        temp_list = [unique_id, level, root.tag, root.attrib['index'], root.attrib['text'], root.attrib['resource-id'], root.attrib['class'], root.attrib['package'], root.attrib['content-desc'], root.attrib['bounds']]
        result_list.append(temp_list)
    unique_id += 1

    # 遍历每个子节点
    children_node = list(root)  # list(root_node) <=> root_node.getchildren()
    if len(children_node) == 0:
        return
    for child in children_node:
        nodeTraversal(child, level + 1, result_list)
    return

# xml文件读取函数，读取完成后返回一个列表[]
def readXml(file_name):
    level = 0  # 用来标记当前节点属于哪一级，节点从深度0开始
    result_list = []  # 初始化一个空的列表
    root = ET.parse(file_name).getroot()  # 获取 xml 文件的根节点
    nodeTraversal(root, level, result_list)  # 从根节点开始遍历

    return result_list


# 删除 csv 文件中的 顶部系统通知栏 部分
def csv_remove_systemNotification(csv_before, csv_after):
    with open(csv_before, 'r', encoding='utf_8_sig') as in_put, open(csv_after, 'w', newline='', encoding='utf_8_sig') as out_put:
        writer = csv.writer(out_put)
        reader = csv.reader(in_put)
        for row in reader:
            if row[7] != 'com.android.systemui':
                writer.writerow(row)

# 删除 csv 文件中 resource-id 为空的节点
def csv_remove_nan_node(csv_before, csv_after):
    with open(csv_before, 'r', encoding='utf_8_sig') as in_put, open(csv_after, 'w', newline='', encoding='utf_8_sig') as out_put:
        writer = csv.writer(out_put)
        reader = csv.reader(in_put)
        for row in reader:
            # 如果 resource-id为空，则删除
            if row[5] == '' or row[5] == 'android:id/content':
                continue
            writer.writerow(row)

def csv_format(csv_before, csv_after):
    temp_i = 0 # 用于截取 android:id/content 及其前面的数据
    # 遍历 csv 文件的
    with open(csv_before, 'r', encoding='utf_8_sig') as in_put, open(csv_after, 'w', newline='', encoding='utf_8_sig') as out_put:
        # 打开csv文件并读取数据
        reader = csv.DictReader(in_put)
        header = reader.fieldnames  # 获取表头
        rows = [row for row in reader]  # 读取 csv 文件的所有行的数据

        # 遍历 csv 文件的行
        for row in rows:
            if row['resource-id'] == 'android:id/content':
                temp_i = int(row['id'])
            # 如果 class 中包含 "android.widget." 则删掉 "android.widget." 且保留其余部分
            if 'android.widget.' in row['class']:
                new_cell = re.sub(r'^android\.widget\.', '', row['class'])  # 删除android.widget.
                row['class'] = new_cell

            # 如果 class 中包含 "LinearLayoutCompat" 则替换成 "androidx.appcompat.widget.LinearLayoutCompat"
            if 'LinearLayoutCompat' in row['class']:
                row['class'] = "androidx.appcompat.widget.LinearLayoutCompat"

            # 如果 class 中包含 "CardView" 则替换成 "androidx.cardview.widget.CardView"
            if 'CardView' in row['class']:
                row['class'] = "androidx.cardview.widget.CardView"

            # 如果 class 中包含 "RecyclerView" 则替换成 "androidx.recyclerview.widget.RecyclerView"
            if 'RecyclerView' in row['class']:
                row['class'] = "androidx.recyclerview.widget.RecyclerView"

            # 如果 class 中包含 "WebView" 则替换成 "WebView"
            if 'WebView' in row['class']:
                row['class'] = "WebView"

            # 如果 class 为 "android.view.View" 则替换成 "View"
            if 'android.view.View' == row['class']:
                row['class'] = "View"

            # 如果 class 为 "android.view.ViewGroup"，则看该字符串所在行的 renderheight 列的值 == 56 && renderwidth 列的值 == 360
            if 'android.view.ViewGroup' == row['class']:
                if (row['x1'] == '0' and row['y1'] == '72' and row['x2'] == '1080' and row['y2'] == '240') or row['height'] == '192':
                    row['class'] = 'androidx.appcompat.widget.Toolbar'
                else:
                    row['class'] = 'androidx.constraintlayout.widget.ConstraintLayout'

            # 如果 resource-id 列有 id，则将前面的 packageName 删掉，保留 ":" 后面的实际 id
            if 'id' in row['resource-id']:
                row['resource-id'] = row['resource-id'].split(':')[1]
                # print(row['resource-id'])

        # 将修改后的数据保存到新的csv文件
        writer = csv.DictWriter(out_put, header)
        writer.writeheader()  # 写入表头
        writer.writerows(rows)  # 写入数据

    with open(csv_after, 'r', encoding='utf-8-sig') as in_put:
        reader = csv.DictReader(in_put)
        header = reader.fieldnames # 获取表头
        # 创建一个空的列表来保存处理后的行数据
        rows_out = []

        # 遍历每一行数据，跳过 resource-id = android:id/content 及其之前的所有节点
        for row in reader:
            # if int(row['id']) <= temp_i:
            #     continue
            # else:
            if row['bounds'] in ['[0,0][1080,1920]', '[0,72][1080,1920]']:
                continue
            # if row['class'] == 'ImageView' and row['resource-id'] == '':
            #     continue
            # elif 'action_bar_root' in row['resource-id'] or 'action_bar_container' in row['resource-id'] or 'decor_content_parent' in row['resource-id']:
            #     continue
            if row['resource-id'] == 'id/action_bar_container' or row['resource-id'] == 'id/content':
                continue
            if row['resource-id'] == '' and row['class'] in ['FrameLayout', 'RelativeLayout']:
                continue
            else:
                rows_out.append(row)

    with open(csv_after, 'w', newline='', encoding='utf-8-sig') as out_put:
        writer = csv.DictWriter(out_put, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows_out)

    # 给当前处理过后的 csv 文件重新设置 id 值
    with open(csv_after, 'r', encoding='utf-8-sig') as in_put:
        reader = csv.reader(in_put)
        data = [row for row in reader]
        # 删除第一列
        for row in data:
            del row[0]
        # 新增"id"列并按序标号
        for i, row in enumerate(data):
            row.insert(0, i)
        data[0][0] = 'id'

        # 在第 2 行插入一组数据
        new_row = [0, 0, "node", 0, "", "id/XMLRoot", "LinearLayout", curPkg, "", "[0,0][1080,1920]", 0, 72, 1080, 1920, 1080, 1920, 360, 640, -1]
        row_index = 1  # 第 2 行的索引为 1
        data.insert(row_index, new_row)

        # 在最后一列后新建 2 列，列名为 "parent_id"，"reuse"
        data[0].append('parent_id')
        data[0].append('reuse')


    with open(csv_after, 'w', newline='', encoding='utf-8-sig') as out_put:
        writer = csv.writer(out_put)
        writer.writerows(data)


# 截取图片中的 ImageView 组件，用于进一步处理
def cut_Image(x1, y1, x2, y2, imgRead, imgSave):
    img = Image.open(imgRead)
    img_width, img_height = img.size

    x1 = max(0, min(x1, img_width))
    y1 = max(0, min(y1, img_height))
    x2 = max(0, min(x2, img_width))
    y2 = max(0, min(y2, img_height))

    cuted = img.crop((x1, y1, x2, y2))
    cuted.save(imgSave)


def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


if __name__ == '__main__':
    # --------------------------------------------------- 先获取截图和原始 xml 文件 -------------------------------------------------- #
    curPkg = getCurrentPackageName()
    print('CurrentPackage:', curPkg)

    # 获取当前界面的activity
    curAct = getCurrentActivity()
    print('CurrentActivity:', curAct)

    # 创建存储当前 App 的 GUI 的文件夹
    appSavePath = 'F:\\YJS\\UI Automator\Save Layout\\' + curPkg
    if not os.path.exists(appSavePath):
        os.makedirs(appSavePath)

    # 定义一些全局变量
    suffix_name = ''
    pngNameBoth = ''  # 保存的截图 /xxx/xxx/xxx/yyy.png

    # 为了避免保存的文件重名，采取循环方式给文件名的最后加数字后缀（由于不可能有超过50个不同界面的Activity相同，所以循环到50）
    for i in range(1, 50):
        suffix_name = curAct + '_' + str(i)
        # 获取保存 UI 截图的名称
        pngNameBoth = appSavePath + '\\' + curAct + '_' + str(i) + '.png'
        # 获取保存 xml文件的名称
        xmlNameBoth = appSavePath + '\\' + curAct + '_' + str(i) + 'temp' + '.xml'

        # 如果这个文件已经存在了, i ++ , 继续下一轮循环
        if os.path.exists(pngNameBoth) == True:
            i += 1
            continue
        # 如果循环到某一次的时候，这个文件还不存在
        else:
            getUIScreenshot(pngNameBoth)  # 保存当前界面的 png 截图
            getUIHierarchy(xmlNameBoth)  # 保存当前界面的 VH 结构

            # 存储完xml文件后对其进行美化工作
            tree = ElementTree.parse(xmlNameBoth)  # 解析xml文件
            root = tree.getroot()  # 得到根元素，Element类
            # 获取美化过的xml文件的名称
            prettyxmlNameBoth = appSavePath + '\\' + curAct + '_' + str(i) + '.xml'
            prettyXml(root, '\t', '\n')    # 调用美化函数
            tree.write(prettyxmlNameBoth)  # 将结果出输出
            os.remove(xmlNameBoth)  # 删掉原来没美化的
            break


    # --------------------------------------------------- 再进一步生成布局代码 ---------------------------------------------------- #
    file_name = suffix_name  # 最终的整体文件名（不带.activity.）

    csvfile_without_systemui = appSavePath + '\\' + file_name + '_without_systemui' + '.csv'
    csvfile_without_useless_node = appSavePath + '\\' + file_name + '_without_useless_node' + '.csv'

    xmlfile = appSavePath + '\\' + file_name + '.xml'  # F:\YJS\UI Automator\Save Layout\包名\文件名.xml

    csvfile = appSavePath + '\\' + file_name + '.csv'  # F:\YJS\UI Automator\Save Layout\包名\文件名.csv
    csvfile_filter = appSavePath + '\\' + file_name + '_filter' + '.csv'  # F:\YJS\UI Automator\Save Layout\包名\文件名.csv

    pngfile = appSavePath + '\\' + file_name + '.png'  # F:\YJS\UI Automator\Save Layout\包名\文件名.png


    # ------------------------------------------------------  创建 x1, y1, x2, y2, width, height, renderwidth, renderheight 列
    R = readXml(xmlfile)  # 读取 xml hierarchy 文件 , R 的类型是列表（List）
    # 从 xml hierarchy 文件中提取 'node', 'index', 'text', 'resource-id', 'package', 'content-desc', 'bounds' 信息，写入新的 csv 文件
    with open(csvfile, 'w', newline='', encoding='utf_8_sig') as fw:  # 以只写的方式打开文件（覆盖原有内容），如果文件不存在，则新建文件并写入
        writer = csv.writer(fw)
        # 创建表头
        writer.writerow(['id', 'level', 'node', 'index', 'text', 'resource-id', 'class', 'package', 'content-desc', 'bounds'])
        for x in R:
            writer.writerow(x)
        fw.close()

    # 读取文件中的bounds列，将数据进行拆分成'x1', 'y1', 'x2', 'y2'，并计算控件宽度 'width'，高度 'height'，渲染宽度 'render_width'，渲染高度 'render_height'
    bounds = pd.read_csv(csvfile, usecols=['bounds'])  # 使用 pandas 库读取指定路径 csv 文件的 'bounds' 列
    data = pd.read_csv(csvfile)

    list_x1 = []
    list_y1 = []
    list_x2 = []
    list_y2 = []
    list_width = []
    list_height = []
    list_render_width = []
    list_render_height = []

    for bound in bounds.values:
        _str = bound[0]  # [0,0][1080,54]
        str1 = _str.replace('][', ',')  # [0,0,1080,54]
        str2 = str1.replace(']', '')  # [0,0,1080,54
        str3 = str2.replace('[', '')  # 0,0,1080,54

        # 将 str3 以 , 进行切片, 分割成4个部分
        x1 = str3.split(',')[0]  # 0
        y1 = str3.split(',')[1]  # 0
        x2 = str3.split(',')[2]  # 1080
        y2 = str3.split(',')[3]  # 54
        width = int(x2) - int(x1)  # 1080
        height = int(y2) - int(y1)  # 54
        render_width = round(float(width / 3), 2)  # 360
        render_height = round(float(height / 3), 2)  # 18

        list_x1 = list_x1 + [x1]
        list_y1 = list_y1 + [y1]
        list_x2 = list_x2 + [x2]
        list_y2 = list_y2 + [y2]
        list_width = list_width + [width]
        list_height = list_height + [height]
        list_render_width = list_render_width + [render_width]
        list_render_height = list_render_height + [render_height]

    data['x1'] = list_x1
    data['y1'] = list_y1
    data['x2'] = list_x2
    data['y2'] = list_y2
    data['width'] = list_width
    data['height'] = list_height
    data['renderwidth'] = list_render_width
    data['renderheight'] = list_render_height

    data.to_csv(csvfile, mode='w', index=False)

    # ------------------------------------------------------  删除界面顶部的系统通知栏信息
    csv_remove_systemNotification(csvfile, csvfile_without_systemui)
    os.remove(csvfile)  # 删掉 原来的csv文件
    os.rename(csvfile_without_systemui, csvfile)  # 将新的 csv 文件重命名为原来的 csv 文件

    # ------------------------------------------------------  将 csv 文件中的 UI 元素进行格式化，变成 Android Studio 需要的格式
    csv_format(csvfile, csvfile_filter)

    # ------------------------------------------------------  将没有 id 的 ImageView / ImageButton 命名
    data = pd.read_csv(csvfile_filter, encoding='utf-8-sig')
    for i, row in data.iterrows():
        if pd.isnull(row['resource-id']) and row['class'] in ['ImageView', 'ImageButton']:
            data.at[i, 'resource-id'] = 'id/' + row['class'] + '_' + str(row['id'])
        # if pd.isnull(row['resource-id']) and row['class'] in ['RelativeLayout', 'LinearLayout']:
        #     data.at[i, 'resource-id'] = 'id/' + row['class']

    data.to_csv(csvfile_filter, mode='w', index=False, encoding='utf-8-sig')

    # ------------------------------------------------------  实现 parent_id 列的数据
    data = pd.read_csv(csvfile_filter, encoding='utf-8-sig')

    # ------ 先处理当前 level > 前一个 level 的情况
    prev_level = None
    prev_id = None

    for i, row in data.iterrows():
        if i == 0: continue

        cur_level = row['level']
        cur_id = row['id']

        if prev_level is not None and cur_level > prev_level:
            data.at[i, 'parent_id'] = prev_id

        prev_level = cur_level
        prev_id = cur_id

    # 将数据保存
    data.to_csv(csvfile_filter, mode='w', index=False, encoding='utf-8-sig')

    # ------ 再处理当前 level <= 前一个 level 的情况
    data = pd.read_csv(csvfile_filter, encoding='utf-8-sig')

    prev_level = None

    for i, row in data.iterrows():
        if i == 0: continue

        cur_level = row['level']

        if prev_level is not None and cur_level <= prev_level:
            for j in range(i - 1, -1, -1):
                if data.loc[j, 'level'] < cur_level:
                    data.at[i, 'parent_id'] = data.loc[j, 'id']
                    break

        prev_level = cur_level

    data.at[1, 'parent_id'] = data.loc[0, 'id']

    # 将数据保存
    data.to_csv(csvfile_filter, mode='w', index=False, encoding='utf-8-sig')


    # ------------------------------------------------------  实现 sibling_id 列的数据
    data = pd.read_csv(csvfile_filter, encoding='utf-8-sig')

    prev_level = None

    for i, row in data.iterrows():
        if i == 0:
            continue  # 跳过根节点，无需判断

        cur_level = row['level']

        # 如果当前节点的 level 值等于上一个节点，则上一个节点就是兄弟节点
        if prev_level is not None and cur_level == prev_level:
            data.at[i, 'sibling_id'] = data.loc[i-1, 'id']

        # 如果当前节点的 level 值小于上一个节点，则不断往前搜索，找到第一个 level 值等于当前节点的，就是兄弟节点
        if prev_level is not None and cur_level < prev_level:
            for j in range(i - 1, -1, -1):
                if data.loc[j, 'level'] == cur_level:
                    data.at[i, 'sibling_id'] = data.loc[j, 'id']
                    break

        prev_level = cur_level

    # 将数据保存
    data.to_csv(csvfile_filter, mode='w', index=False, encoding='utf-8-sig')


    data = pd.read_csv(csvfile_filter, encoding='utf-8-sig')
    data['sibling_id'] = data['sibling_id'].fillna(-1)  # 将 sibling_id 列中的空值替换为 -1
    data.to_csv(csvfile_filter, mode='w', index=False, encoding='utf-8-sig')


    # ------------------------------------------------------  实现 reuse 列的数据

    # 读取 CSV 文件
    data = pd.read_csv(csvfile_filter, encoding='utf-8-sig')

    # 判断 'resource-id' 列是否有重复元素
    duplicated = data['resource-id'].duplicated(keep=False)

    # 将 'reuse' 列根据 resource-id 是否重复，设置为 true 或 false，注：空值也算重复
    data.loc[duplicated, 'reuse'] = 'true'
    data.loc[~duplicated, 'reuse'] = 'false'

    # 遍历 'resource-id' 列，单独处理空值的情况
    for index, row in data.iterrows():
        # 如果 'resource-id' 列的值为 空 且 'class' 列不是 RelativeLayout 或 LinearLayout，则将 'reuse' 列设置为 false
        if pd.isna(row['resource-id']): # and row['class'] not in ['RelativeLayout', 'LinearLayout']:
            data.at[index, 'reuse'] = 'false'

    # 将修改后的数据写回 CSV 文件
    data.to_csv(csvfile_filter, index=False, encoding='utf-8-sig')


    # ------------------------------------------------------  根据处理过的 csv 文件绘制线框图
    # 首先找到文件的路径
    picture1 = 'F:\\YJS\\UI Automator\\blank.png'  # 空白底的图片
    picture2 = pngfile  # 原始图片

    image1 = Image.open(picture1)  # 打开一张图片
    image2 = Image.open(picture2)  # 打开一张图片

    draw1 = ImageDraw.Draw(image1)  # 在上面画画
    draw2 = ImageDraw.Draw(image2)  # 在上面画画

    data = pd.read_csv(csvfile_filter)

    coordinates = pd.read_csv(csvfile_filter, usecols=['x1', 'y1', 'x2', 'y2'])  # 坐标：读取指定路径 csv 文件的 x1, y1, x2, y2 列

    for coordinate in coordinates.values:
        x1 = coordinate[0]
        y1 = coordinate[1]
        x2 = coordinate[2]
        y2 = coordinate[3]
        draw1.rectangle([x1, y1, x2, y2], width=5, outline=(255, 0, 0))  # [左上角x，左上角y，右下角x，右下角y]，outline边框颜色
        draw2.rectangle([x1, y1, x2, y2], width=5, outline=(255, 0, 0))  # [左上角x，左上角y，右下角x，右下角y]，outline边框颜色

    image1.save(appSavePath + '\\' + file_name + '_with_blank_wireframe' + '.png')
    image2.save(appSavePath + '\\' + file_name + '_with_wireframe' + '.png')

    # ------------------------------------------------------ 利用前面处理过的最终 csv 文件来创建 xml 布局代码

    # 创建存储 ImageView/ImageButton 的文件夹
    imageViewPath = appSavePath + '\\' + suffix_name + '\\ImageView'
    if not os.path.exists(imageViewPath):
        os.makedirs(imageViewPath)

    # 创建存储 TextView 的文件夹
    textViewPath = appSavePath + '\\' + suffix_name + '\\TextView'
    if not os.path.exists(textViewPath):
        os.makedirs(textViewPath)

    # 创建存储 ToolBar 的文件夹
    toolBarPath = appSavePath + '\\' + suffix_name + '\\ToolBar'
    if not os.path.exists(toolBarPath):
        os.makedirs(toolBarPath)

    # 创建存储 CardView 的文件夹
    cardViewPath = appSavePath + '\\' + suffix_name + '\\CardView'
    if not os.path.exists(cardViewPath):
        os.makedirs(cardViewPath)

    # 创建存储复用 xml 代码的文件夹
    reuseXmlPath = appSavePath + '\\' + suffix_name + '\\ReuseXmlCode'
    if not os.path.exists(reuseXmlPath):
        os.makedirs(reuseXmlPath)

    # 创建存储 Layout 的文件夹
    linearLayoutPath = appSavePath + '\\' + suffix_name + '\\LayoutPath'
    if not os.path.exists(linearLayoutPath):
        os.makedirs(linearLayoutPath)

    # 读取的截图文件：
    readScreenshot = pngfile

    # 保存 ImageView 的路径
    savaImageViewPath = imageViewPath + '\\'

    # 保存 TextView 的路径
    savaTextViewPath = textViewPath + '\\'

    # 保存 ToolBar 的路径
    savaToolBarPath = toolBarPath + '\\'

    # 保存 CardView 的路径
    savaCardViewPath = cardViewPath + '\\'

    # 保存 Layout 的路径
    savaLayoutPath = linearLayoutPath + '\\'


    # 读取 csv 文件，把需要保留的信息存到 DataFrame 中
    df = pd.read_csv(csvfile_filter, usecols=['id', 'level', 'text', 'resource-id', 'class', 'content-desc', 'x1', 'y1', 'x2', 'y2', 'renderwidth', 'renderheight', 'parent_id', 'reuse','sibling_id'])

    # 定义要用到的全局变量
    n = len(df) + 1                     # 定义 csv 文件的行数 n
    _list = [[] for i in range(n)]      # 定义一个具有 n 行的 空列表，用来存储 将各个节点插入到 xml 文件后的返回值
    node_list = [[] for i in range(n)]  # 定义一个具有 n 行的 空列表，用来存所有遍历过的节点 (lxml.etree._Element类型)
    hash_set = set()                    # 定义一个哈希集合，用于存已经单独创建过 xml 文件的节点的 resource-id
    row_id = 0                          # 表示当前数据所在行数，相对布局的根节点在 0 行，其余组件节点从 1 行开始

    android_namespace = "{http://schemas.android.com/apk/res/android}"  # 注册命名空间 android
    app_namespace = "{http://schemas.android.com/apk/res-auto}"         # 注册命名空间 tool


    # 接下来要正式开始创建 xml 布局文件

    # 创建根节点：<LinearLayout> 并将根节点加入 node_list 列表
    root = etree.Element("LinearLayout", nsmap={'android': 'http://schemas.android.com/apk/res/android', 'app': 'http://schemas.android.com/apk/res-auto'})
    root.set(android_namespace + 'id', '@+id/XMLRoot')
    root.set(android_namespace + 'orientation', 'vertical')
    root.set(android_namespace + 'layout_width', 'match_parent')
    root.set(android_namespace + 'layout_height', 'match_parent')

    colors = extcolors.extract_from_path(pngNameBoth, tolerance=12, limit=12)  # 提取 整张截图 中的颜色
    color_1_R = str(hex(colors[0][0][0][0])[2:].upper().rjust(2, '0'))
    color_1_G = str(hex(colors[0][0][0][1])[2:].upper().rjust(2, '0'))
    color_1_B = str(hex(colors[0][0][0][2])[2:].upper().rjust(2, '0'))
    color_1 = '#' + color_1_R + color_1_G + color_1_B  # color_1 表示最多的颜色，作为背景色

    root.set(android_namespace + 'background', color_1)

    node_list[0] = root

    # 遍历 DataFrame 的每一行
    for data in df.values:
        if row_id == n:
            break

        # 注：csv 文件里的空值会被提取成 "nan"，且默认以 float 类型存储 "nan"
        _id = int(data[0])
        _level = int(data[1])
        _text = str(data[2])
        _resource_id = str(data[3])
        _class = data[4]
        _content_des = str(data[5])
        _x1 = int(int(data[6]) / 3)
        _y1 = int((int(data[7]) - 72) / 3)
        _x2 = int(int(data[8]) / 3)
        _y2 = int((int(data[9]) - 72) / 3)
        _width = float(data[10])  # 渲染宽度为 360 表示 match_parent
        _height = float(data[11])  # 渲染高度为 640 表示 match_parent
        _parent_id = int(data[12])
        _reuse = str(data[13])
        _sibling_id = int(data[14])


        x_1 = int(data[6])  # 原始的 x1 坐标值，在分割图片时用
        y_1 = int(data[7])  # 原始的 y1 坐标值，在分割图片时用
        x_2 = int(data[8])  # 原始的 x2 坐标值，在分割图片时用
        y_2 = int(data[9])  # 原始的 y2 坐标值，在分割图片时用

        # 将所需数据预处理到一个二维数组 _list 中，_list[i] 表示 csv 文件的第 i 行的数据
        _list[row_id].append(_id)           # _list[row_id][0]  -> id
        _list[row_id].append(_level)        # _list[row_id][1]  -> level
        _list[row_id].append(_text)         # _list[row_id][2]  -> text
        _list[row_id].append(_resource_id)  # _list[row_id][3]  -> resource_id
        _list[row_id].append(_class)        # _list[row_id][4]  -> class
        _list[row_id].append(_content_des)  # _list[row_id][5]  -> description
        _list[row_id].append(_x1)           # _list[row_id][6]  -> x1
        _list[row_id].append(_y1)           # _list[row_id][7]  -> y1
        _list[row_id].append(_x2)           # _list[row_id][8]  -> x2
        _list[row_id].append(_y2)           # _list[row_id][9]  -> y2
        _list[row_id].append(str(_width))   # _list[row_id][10] -> renderwidth
        _list[row_id].append(str(_height))  # _list[row_id][11] -> renderheight
        _list[row_id].append(_parent_id)    # _list[row_id][12] -> parent_id
        _list[row_id].append(_reuse)        # _list[row_id][13] -> reuse
        _list[row_id].append(_sibling_id)   # _list[row_id][14] -> sibling_id


        # ----------------- 接下来创建除根节点以外的各具体节点

        # 跳过第 0 行，即 根节点 所在的行，这样一来，row_id 就能与 node_id 一一对应
        if row_id == 0:
            row_id += 1
            continue

        # 当前节点 id
        node_id = _list[row_id][0]

        # 当前节点 resource_id，用于生成复用 UI 节点
        node_resource_id = ''
        if _list[row_id][3] != 'nan':
            node_resource_id = _list[row_id][3].split('/')[1].lower()


        # 当前节点 类型
        node_class = _list[row_id][4]

        # 当前节点的父节点 id
        parent_node_id = _list[row_id][12]

        # 当前节点的上一个兄弟节点的 id
        sibling_node_id = _list[row_id][14]

        # 当前节点的父节点 class
        parent_node_class = _list[parent_node_id][4]

        # 父节点 resource_id
        parent_node_resource_id = ''
        if _list[parent_node_id][3] != 'nan':
            parent_node_resource_id = _list[parent_node_id][3].split('/')[1].lower()

        # 当前节点的父节点（'lxml.etree._Element' 类型的）
        parent_node = node_list[parent_node_id]


        # 在创建节点前，先判断是不是被复用的节点 ！！！
        if _list[row_id][13] == 'True' and parent_node_class in ['androidx.recyclerview.widget.RecyclerView', 'ListView', 'GridView', 'Snipper']:

            # 如果在哈希表中已经存在了，则说明已经生成过 xml 了，跳过
            if node_resource_id in hash_set:
                row_id += 1
                continue
            # 否则，还没有被生成过
            else:
                # 将当前节点的 resource-id 记录到哈希集合中，表示当前节点已经生成过复用代码
                hash_set.add(node_resource_id)
                # 如果当前出现重复的节点的父节点是 四种 布局节点的话，创建 xml 文件，将当前节点作为其父节点的子节点
                if parent_node_class in ['androidx.recyclerview.widget.RecyclerView', 'ListView', 'GridView', 'Snipper']:
                    # 将当前节点创建到单独的 xml 文件中，命名为 ActivityName + '_item.xml'

                    # 如果哈希集合中的组件个数 == 1，则创建根节点 FrameLayout，再将当前节点拼接到 根节点 下面
                    if len(hash_set) == 1:
                        # ------------ 先创建 复用 xml 代码的根节点：<FrameLayout>
                        reuseroot = etree.Element("FrameLayout", nsmap={'android': 'http://schemas.android.com/apk/res/android'})
                        reuseroot.set(android_namespace + 'layout_width', 'wrap_content')
                        reuseroot.set(android_namespace + 'layout_height', 'wrap_content')

                        # ------------ 再创建当前节点：reuse_node
                        reuse_node = etree.Element(node_class)

                        # 如果当前节点有 resource-id，则创建 android:id 属性
                        if _list[row_id][3] != 'nan':
                            reuse_node.set(android_namespace + 'id', '@+' + _list[row_id][3])  # 设置 id

                        # 设置节点的宽高（特别地，如果是 FrameLayout 则设置宽高为 wrap_content）
                        if node_class == 'FrameLayout':
                            reuse_node.set(android_namespace + 'layout_width', 'wrap_content')  # 宽
                            reuse_node.set(android_namespace + 'layout_height', 'wrap_content')  # 高
                        else:
                            reuse_node.set(android_namespace + 'layout_width', _list[row_id][10] + 'dp')   # 宽
                            reuse_node.set(android_namespace + 'layout_height', _list[row_id][11] + 'dp')  # 高

                        # 如果当前节点是 ImageView 或 ImageButton，则将图片截取出来保存
                        if _list[row_id][4] in ['ImageView', 'ImageButton']:
                            _image_view_name = _list[row_id][3].split('/')[1].lower() + '_' + str(_list[row_id][0])  # 图片名称: id/avatar_29 只取 avatar_29，然后加 _id
                            cut_Image(x_1, y_1, x_2, y_2, readScreenshot, savaImageViewPath + _image_view_name + '.png')

                        # ------------ 将 reuse_node 接到根节点 reuse_root 上
                        reuseroot.append(reuse_node)

                        # ------------ 最后将 xml 文件保存

                        etree.indent(reuseroot, space='    ')  # 在每个新建节点前 加 4 个空格

                        # 创建一个 ElementTree 结构
                        reusetree = etree.ElementTree(reuseroot)

                        reusexml_layout_file = reuseXmlPath + '\\' + curAct + '_item' + '.xml'

                        # 将 ElementTree 结构写入新的 xml 文件
                        reusetree.write(reusexml_layout_file, pretty_print=True)

                    # 如果哈希集合中的组件个数 > 1，则不要创建根节点，直接打开现有 xml 文件，将当前节点拼接到 根节点 下面
                    if len(hash_set) > 1:
                        # 打开 xml 文件并解析
                        reusexml_layout_file = reuseXmlPath + '\\' + curAct + '_item' + '.xml'
                        tree = etree.parse(reusexml_layout_file)
                        reuseroot = tree.getroot()

                        # ------------ 再创建当前节点：reuse_node
                        reuse_node = etree.Element(node_class)

                        # 如果当前节点有 resource-id，则创建 android:id 属性
                        if _list[row_id][3] != 'nan':
                            reuse_node.set(android_namespace + 'id', '@+' + _list[row_id][3])  # 设置 id

                        # 设置节点的宽高（特别地，如果是 FrameLayout 则设置宽高为 wrap_content）
                        if node_class == 'FrameLayout':
                            reuse_node.set(android_namespace + 'layout_width', 'wrap_content')  # 宽
                            reuse_node.set(android_namespace + 'layout_height', 'wrap_content')  # 高
                        else:
                            reuse_node.set(android_namespace + 'layout_width', _list[row_id][10] + 'dp')  # 宽
                            reuse_node.set(android_namespace + 'layout_height', _list[row_id][11] + 'dp')  # 高

                        # 如果当前节点是 ImageView 或 ImageButton，则将图片截取出来保存
                        if _list[row_id][4] in ['ImageView', 'ImageButton']:
                            _image_view_name = _list[row_id][3].split('/')[1].lower() + '_' + str(
                                _list[row_id][0])  # 图片名称: id/avatar_29 只取 avatar_29，然后加 _id
                            cut_Image(x_1, y_1, x_2, y_2, readScreenshot, savaImageViewPath + _image_view_name + '.png')

                        # ------------ 将 reuse_node 接到根节点 reuse_root 上
                        reuseroot.append(reuse_node)

                        # ------------ 最后将 xml 文件保存

                        etree.indent(reuseroot, space='    ')  # 在每个新建节点前 加 4 个空格

                        # 创建一个 ElementTree 结构
                        reusetree = etree.ElementTree(reuseroot)

                        reusexml_layout_file = reuseXmlPath + '\\' + curAct + '_item' + '.xml'

                        # 将 ElementTree 结构写入新的 xml 文件
                        reusetree.write(reusexml_layout_file, pretty_print=True)


                    # 一轮循环后，行号 + 1
                    row_id += 1

                # 如果当前出现重复的节点的父节点是不是 四种 布局节点的话，打开 xml 文件，将当前节点作为其父节点的子节点
                else:
                    # 打开 xml 文件并解析
                    reusexml_layout_file = reuseXmlPath + '\\' + curAct + '_item' + '.xml'
                    tree = etree.parse(reusexml_layout_file)

                    # 定义要查找的元素名称和属性值
                    element_name = parent_node_class
                    attribute_name = 'android:id'
                    attribute_value = '@+id/' + parent_node_resource_id

                    # 定义命名空间前缀和 URI
                    ns = {'android': 'http://schemas.android.com/apk/res/android'}

                    # 查找满足条件的节点 p
                    xpath = ".//{0}[@{1}='{2}']".format(element_name, attribute_name, attribute_value)
                    p = tree.find(xpath, ns)  # 从树结构中查找具有指定属性名称和属性值的元素，并将其赋值给 p

                    # 创建子节点及其属性
                    reuse_node = etree.Element(node_class)

                    # 如果当前节点有 resource-id，则创建 android:id 属性
                    if _list[row_id][3] != 'nan':
                        reuse_node.set(android_namespace + 'id', '@+' + _list[row_id][3])  # 设置 id

                    # 设置宽高
                    reuse_node.set(android_namespace + 'layout_width', _list[row_id][10] + 'dp')   # 宽
                    reuse_node.set(android_namespace + 'layout_height', _list[row_id][11] + 'dp')  # 高

                    # 将子节点接到对应的父节点上
                    p.append(reuse_node)

                    # 将修改后的 xml 文件保存
                    etree.indent(tree, space='    ')  # 在每个新建节点前 加 4 个空格
                    tree.write(reusexml_layout_file, pretty_print=True)

                    # 一轮循环后，行号 + 1
                    row_id += 1

        # 如果不是被复用的节点
        else:
            # 创建当前节点（'lxml.etree._Element' 类型）
            node = etree.Element(node_class)

            # 如果当前节点有描述，则将该描述写到当前节点的注释中
            if _list[row_id][5] != 'nan':
                node.insert(0, etree.Comment(_list[row_id][5]))

            # ----- 设置 android:id： 如果当前节点有 resource-id，则创建 android:id 属性
            if _list[row_id][3] != 'nan':
                node.set(android_namespace + 'id', '@+' + _list[row_id][3])  # 设置 id

            # ----- 设置 背景颜色
            # ----- 如果是 ToolBar 则额外设置其背景色 android:background
            if node_class == 'androidx.appcompat.widget.Toolbar':
                # 确定 ToolBar 的名称
                _toolbar_name = _list[node_id][3].split('/')[1].lower()
                # 根据 ToolBar 的坐标，从一个截图中裁剪出相应区域，并将结果保存到一个图片文件中
                cut_Image(x_1, y_1, x_2, y_2, readScreenshot, savaToolBarPath + _toolbar_name + '.png')

                tbr = savaToolBarPath + _toolbar_name + '.png'
                colors = extcolors.extract_from_path(tbr, tolerance=12, limit=12)  # 提取 TextView 图片中的颜色
                color_1_R = str(hex(colors[0][0][0][0])[2:].upper().rjust(2, '0'))
                color_1_G = str(hex(colors[0][0][0][1])[2:].upper().rjust(2, '0'))
                color_1_B = str(hex(colors[0][0][0][2])[2:].upper().rjust(2, '0'))
                color_1 = '#' + color_1_R + color_1_G + color_1_B  # color_1 表示最多的颜色，作为背景色
                node.set(android_namespace + 'background', color_1)
                node.set(app_namespace + 'contentInsetStart', '0dp')

            # ----- 如果是某些布局，则设置其背景色
            if node_class == 'LinearLayout':
                # 根据 LinearLayout 的坐标，从一个截图中裁剪出相应区域，并将结果保存到一个图片文件中
                cut_Image(x_1, y_1, x_2, y_2, readScreenshot, savaLayoutPath + '' + str(i) + '.png')

                ll = savaLayoutPath + '' + str(i) + '.png'
                colors = extcolors.extract_from_path(ll, tolerance=12, limit=12)  # 提取 TextView 图片中的颜色
                color_1_R = str(hex(colors[0][0][0][0])[2:].upper().rjust(2, '0'))
                color_1_G = str(hex(colors[0][0][0][1])[2:].upper().rjust(2, '0'))
                color_1_B = str(hex(colors[0][0][0][2])[2:].upper().rjust(2, '0'))
                color_1 = '#' + color_1_R + color_1_G + color_1_B  # color_1 表示最多的颜色，作为背景色
                # node.set(android_namespace + 'background', color_1)

            # ----- 如果是 CardView 则额外设置其背景色 app:cardBackgroundColor   savaCardViewPath
            if node_class == 'androidx.cardview.widget.CardView':
                # 确定 CardView 的名称
                _cardview_name = _list[node_id][3].split('/')[1].lower()
                # 根据 CardView 的坐标，从一个截图中裁剪出相应区域，并将结果保存到一个图片文件中
                cut_Image(x_1, y_1, x_2, y_2, readScreenshot, savaCardViewPath + _cardview_name + '.png')

                crdv = savaCardViewPath + _cardview_name + '.png'
                colors = extcolors.extract_from_path(crdv, tolerance=12, limit=12)  # 提取 TextView 图片中的颜色
                color_1_R = str(hex(colors[0][0][0][0])[2:].upper().rjust(2, '0'))
                color_1_G = str(hex(colors[0][0][0][1])[2:].upper().rjust(2, '0'))
                color_1_B = str(hex(colors[0][0][0][2])[2:].upper().rjust(2, '0'))
                color_1 = '#' + color_1_R + color_1_G + color_1_B  # color_1 表示最多的颜色，作为背景色
                node.set(app_namespace + 'cardBackgroundColor', color_1)


            # ----- 设置宽度 android:layout_width 和高度 android:layout_height
            if node_class == 'FrameLayout':  # 对于 FrameLayout，宽高都设置为 wrap_content
                node.set(android_namespace + 'layout_width', 'wrap_content')  # 宽
                node.set(android_namespace + 'layout_height', 'wrap_content')  # 高
            else:  # 对于 其他布局，宽高都设置为实际的 dp 值
                node.set(android_namespace + 'layout_width', _list[row_id][10] + 'dp')  # 宽
                node.set(android_namespace + 'layout_height', _list[row_id][11] + 'dp')  # 高

            # 设置位置属性 ---- 根据父节点类型是否为 RelativeLayout 分类讨论
            layout_marginLeft = ''
            layout_marginTop = ''

            # 如果父节点类型是 RelativeLayout
            if parent_node_class == 'RelativeLayout':
                # 如果当前组件是其父节点的第一个节点，则没有上一个兄弟节点，根据父节点定位：
                if sibling_node_id == -1:
                    layout_marginTop = str(_list[row_id][7] - _list[parent_node_id][7]) + 'dp'
                    layout_marginLeft = str(_list[row_id][6] - _list[parent_node_id][6]) + 'dp'
                    node.set(android_namespace + 'layout_marginLeft', layout_marginTop)
                    node.set(android_namespace + 'layout_marginTop', layout_marginLeft)
                # 否则，如果当前组件不是其父节点的第一个节点，则根据上一个兄弟节点定位：
                else:
                    # 如果 node_id.y1 >= sibling_node_id.y2 则在上一个兄弟节点的下边，则利用左右关系定位
                    if _list[row_id][7] >= _list[sibling_node_id][9]:
                        node.set(android_namespace + 'layout_below', '@+' + _list[sibling_node_id][3])
                        layout_marginTop = str(_list[row_id][7] - _list[sibling_node_id][9]) + 'dp'  # marginTop 根据兄弟节点定位
                        layout_marginLeft = str(_list[row_id][6] - _list[parent_node_id][6]) + 'dp'  # marginLeft 根据父节点定位
                        node.set(android_namespace + 'layout_marginTop', layout_marginTop)
                        node.set(android_namespace + 'layout_marginLeft', layout_marginLeft)

                    # 如果 node_id.x1 >= sibling_node_id.x2 则在上一个兄弟节点的右边，则利用上下关系定位
                    elif _list[row_id][6] >= _list[sibling_node_id][8]:
                        node.set(android_namespace + 'layout_toRightOf', '@+' + _list[sibling_node_id][3])
                        layout_marginLeft = str(_list[row_id][6] - _list[sibling_node_id][8]) + 'dp'  # marginLeft 根据兄弟节点定位
                        layout_marginTop = str(_list[row_id][7] - _list[parent_node_id][7]) + 'dp'    # marginTop 根据父节点定位
                        node.set(android_namespace + 'layout_marginLeft', layout_marginLeft)
                        node.set(android_namespace + 'layout_marginTop', layout_marginTop)


            # 如果父节点类型不是 RelativeLayout
            else:
                # 如果父节点类型是 ToolBar，则符合水平方向上的分布
                if parent_node_class == 'androidx.appcompat.widget.Toolbar':
                    layout_marginTop = str(_list[row_id][7] - _list[parent_node_id][7]) + 'dp'  # layout_marginTop 属性只根据父节点定位
                    if node_id - 1 == parent_node_id:  # 如果上一个节点是父节点，则 layout_marginLeft 属性根据父节点定位
                        layout_marginLeft = str(_list[row_id][6] - _list[parent_node_id][6]) + 'dp'
                    else:  # 如果上一个节点是兄弟节点，则 layout_marginLeft 属性根据兄弟节点定位
                        layout_marginLeft = str(_list[row_id][6] - _list[sibling_node_id][8]) + 'dp'

                # 否则，只要父节点类型不是 ToolBar，则符合垂直方向上的分布
                if parent_node_class != 'androidx.appcompat.widget.Toolbar':
                    # if node_id - 1 == parent_node_id or parent_node_id == 0:
                    if node_id - 1 == parent_node_id:  # 如果上一个节点是父节点，则 layout_marginTop 属性根据父节点定位
                        layout_marginTop = str(_list[row_id][7] - _list[parent_node_id][7]) + 'dp'
                    elif sibling_node_id == -1:
                        layout_marginTop = str(_list[row_id][7] - _list[parent_node_id][7]) + 'dp'
                    else:  # 如果上一个节点是兄弟节点，则 layout_marginTop 属性根据兄弟节点定位
                        layout_marginTop = str(_list[row_id][7] - _list[sibling_node_id][9]) + 'dp'

                    layout_marginLeft = str(_list[row_id][6] - _list[parent_node_id][6]) + 'dp'  # layout_marginLeft 属性只根据父节点定位
                node.set(android_namespace + 'layout_marginLeft', layout_marginLeft)  # 距屏幕左侧距离
                node.set(android_namespace + 'layout_marginTop', layout_marginTop)    # 距屏幕顶部距离

            # 对于 LinearLayout 设置 orientation 属性
            if node_class == 'LinearLayout' or node_class == 'androidx.appcompat.widget.LinearLayoutCompat':
                node.set(android_namespace + 'orientation', 'vertical')  # 先设置成 vertical，如果后续发现不是，再修改成 horizontal

            # 如果当前节点有文本，则创建 text 属性
            if _list[row_id][2] != 'nan':
                node.set(android_namespace + 'text', _list[row_id][2])

            # 特判组件的类型是不是图片：
            # 如果是 ImageView，则加上引用的属性：android:src="@drawable/图片名"
            if node_class == 'ImageView':
                _image_view_name = _list[row_id][3].split('/')[1].lower() + '_' + str(_list[row_id][0])  # 图片名称: id/avatar_29 只取 avatar_29，然后加 _id
                node.set(android_namespace + 'src', '@drawable/' + _image_view_name)
                cut_Image(x_1, y_1, x_2, y_2, readScreenshot, savaImageViewPath + _image_view_name + '.png')
            # 如果是 ImageButton，则加上引用的属性：android:background="@drawable/图片名"
            if node_class == 'ImageButton':
                _image_view_name = _list[row_id][3].split('/')[1].lower() + '_' + str(_list[row_id][0])  # 图片名称: id/avatar_29 只取 avatar_29，然后加 _id
                node.set(android_namespace + 'background', '@drawable/' + _image_view_name)
                cut_Image(x_1, y_1, x_2, y_2, readScreenshot, savaImageViewPath + _image_view_name + '.png')


            # 特判组件的类型是不是文本：
            # 如果是 TextView，则加上文字大小自适应属性：app:autoSizeTextType="uniform" 以及字体颜色
            if node_class in ['TextView', 'CheckBox', 'RadioButton', 'Switch', 'ToggleButton', 'EditText', 'AutoCompleteTextView', 'Button']:
                # 确定 TextView 的名称
                _text_view_name = 'textview_' + str(_list[row_id][0])

                # 根据 TextView 的坐标，从一个截图中裁剪出相应区域，并将结果保存到一个图片文件中
                cut_Image(x_1, y_1, x_2, y_2, readScreenshot, savaTextViewPath + _text_view_name + '.png')

                # 第一行定义了一个变量 textImg，表示 TextView 图片的路径
                # 第二行使用 extcolors 库中的 extract_from_path 方法从图片中提取颜色信息，tolerance 参数表示颜色匹配的容差，limit 参数表示提取的颜色数量的限制
                # 第三至八行分别从提取的颜色信息中获取第一种和第二种颜色的 R、G、B 值，并将其转化为 16 进制字符串表示的形式，并在前面加上 # 号，表示颜色的格式
                # 第九至十一行分别将获取到的颜色信息设置为 TextView 的背景色和文本颜色，使用了 Android 命名空间和应用命名空间中的属性名
                # 最后一行设置了 TextView 的文本自动调整大小属性为 uniform，表示文本会根据 TextView 的大小自动调整字号

                textImg = savaTextViewPath + _text_view_name + '.png'
                colors = extcolors.extract_from_path(textImg, tolerance=12, limit=12)  # 提取 TextView 图片中的颜色

                color_1_R = str(hex(colors[0][0][0][0])[2:].upper().rjust(2, '0'))
                color_1_G = str(hex(colors[0][0][0][1])[2:].upper().rjust(2, '0'))
                color_1_B = str(hex(colors[0][0][0][2])[2:].upper().rjust(2, '0'))
                color_1 = '#' + color_1_R + color_1_G + color_1_B  # color_1 表示最多的颜色，作为背景色
                node.set(android_namespace + 'background', color_1)

                if len(colors[0]) > 1:
                    color_2_R = str(hex(colors[0][1][0][0])[2:].upper().rjust(2, '0'))
                    color_2_G = str(hex(colors[0][1][0][1])[2:].upper().rjust(2, '0'))
                    color_2_B = str(hex(colors[0][1][0][2])[2:].upper().rjust(2, '0'))
                    color_2 = '#' + color_2_R + color_2_G + color_2_B  # color_2 表示第二多的颜色，作为文本色
                    node.set(android_namespace + 'textColor', color_2)
                    # node.set(app_namespace + 'autoSizeTextType', "uniform")


            # 将当前节点插入到其父节点下
            parent_node.append(node)

            # 将当前节点保存到 node_list 列表中
            node_list[node_id] = node

            # 一轮循环后，行号 + 1
            row_id += 1


        # 利用 indent函数 进行缩进，需要python3.9 +
        etree.indent(root, space='    ')  # 在每个新建节点前 加 4 个空格


        # 创建一个 ElementTree 结构
        tree = etree.ElementTree(root)

        xml_layout_file = appSavePath + '\\' + file_name + '_layout' + '.xml'

        # 将 ElementTree 结构写入新的 xml 文件
        tree.write(xml_layout_file, pretty_print=True)



