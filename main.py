# -*- coding:utf-8 -*-
# -------------------------------------------------------------------------------
# Name:        Object bounding box label tool
# Purpose:     Label object bounding boxes for Detection
# Author:      HUST
# Created:     08/06/2018
#-------------------------------------------------------------------------------
from tkinter import messagebox, filedialog
from tkinter import *
from PIL import Image, ImageTk
import numpy as np
import xml.dom.minidom
import xml.dom
import glob
import os

# colors for the bboxes
COLORS = ['red', 'orange', 'cyan', 'green', 'blue', 'purple', 'pink', 'black', 'gray']
# classes name
CLASSES = ['aeroplane', 'bicycle', 'bird', 'boat', 'bottle', 'bus',
           'car', 'cat', 'chair', 'cow', 'diningtable', 'dog', 'horse',
           'motorbike', 'person', 'pottedplant', 'sheep', 'sofa',
           'train', 'tvmonitor']

# Some parameters for VOC label
_POSE = 'Unspecified'
_TRUNCATED = '0'
_DIFFICULT = '0'
_SEGMENTED = '0'

class LabelTool:
    def __init__(self, master):
        self.parent = master
        self.parent.title("LabelTool")
        self.w, self.h =  self.parent.maxsize()
        # self.parent.geometry('%dx%d' %(w, h))
        self.parent.state('zoomed')
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)

        # initialize mouse state
        self.STATE = {'click': 0, 'x': 0, 'y': 0}

        # initialize global state
        self.flag = 0
        self.imageList = []     # The list for images path.
        self.outDir = './Labels'    # The path of labelled annotations.
        self.cur = 0    # The index of images path.
        self.total = 0     # The total images.
        self.del_num = 0    # The number of deleted images.
        self.image_name = ''    # The name of precessing image.
        self.label_filename = ''    # The name of .xml.
        self.label_filename1 = ''   # The name of .txt, it's used to check annotations.
        self.tkimg = None   # Image displayed on canvas.
        self.img = None
        self.width = 0     # The size of origin image.
        self.height = 0    # The size of origin image.
        self.depth = 0     # The size of origin image.
        self.color_map = COLORS[0]   # The color of bounding boxes.
        self.class_name = None     # The class name of right-click.
        self.classes_name = []     # All classes of a image.
        self.bboxIdLine = []
        self.bboxIdList = []     # Save drawing handle.
        self.classIdList = []    # Save text handle.
        self.bboxId = None     # Drawing handle.
        self.bboxList = []     # Save all bounding boxes.
        self.hl = None      # Horizontal line.
        self.vl = None      # Vertical line.
        self.coordinate = []
        self.x1 = 0
        self.y1 = 0
        self.xx1 = 0
        self.x2 = 0
        self.yy1 = 0
        self.y2 = 0

        # dir entry & load
        radio_var = IntVar()
        self.label = Label(self.frame, text = 'Label Type:')
        self.label.place(x = 10, y = 10, width = 70, height = 16)
        self.rad = Radiobutton(self.frame, text = 'rectangle', variable = radio_var, value = 1, command = self.Rectangle)
        self.rad.place(x = 90, y = 10, width = 80, height = 16)
        self.rad1 = Radiobutton(self.frame, text = 'polygon', variable = radio_var, value = 2, command = self.Polygon)
        self.rad1.place(x = 180, y = 10, width = 80, height = 16)

        self.label1 = Label(self.frame, text = "Image Path:")
        self.label1.place(x = 10, y = 40, width = 71, height = 16)
        self.label2 = Entry(self.frame)
        self.label2.place(x = 90, y = 40, width = 255, height = 20)
        self.label3 = Label(self.frame, text = "Image Size:")
        self.label3.place(x = 10, y = 70, width = 71, height = 16)
        self.label4 = Label(self.frame, bg='white')
        self.label4.place(x = 90, y = 70, width = 171, height = 16)
        self.label5 = Label(self.frame, text = "Bounding Box:")
        self.label5.place(x = 3, y = 100, width = 101, height = 16)
        self.label6 = Label(self.frame, text =  "Doing:     /    ")
        self.label6.place(x = 120, y = 100 , width = 150, height = 16)
        self.label7 = Label(self.frame, bg = 'white', fg = 'red', anchor = W, text = "x: ")
        self.label7.place(x = 270, y = 120, width = 75, height = 20)
        self.label8 = Label(self.frame, bg = 'white', fg = 'red', anchor = W, text = "y: ")
        self.label8.place(x = 270, y = 145, width = 75, height = 20)

        self.button = Button(self.frame, text = "Load Image", state = 'disabled', command = self.Load_image)
        self.button.place(x = 270, y = 70, width = 75, height = 20)
        self.button1 = Button(self.frame, text = "Delete", state = 'disabled', command = self.delBBox)
        self.button1.place(x = 270, y = 190, width = 75, height = 20)
        self.button2 = Button(self.frame, text = "ClearAll", state = 'disabled', command = self.clearBBox)
        self.button2.place(x = 270, y = 220, width = 75, height = 20)
        self.button3 = Button(self.frame, text = "<< Prev", state = 'disabled', command = self.prevImage)
        self.button3.bind_all('w', self.prevImage)
        self.button3.bind_all('a', self.prevImage)
        self.button3.place(x = 10, y = 250, width = 65, height = 20)
        self.button4 = Button(self.frame, text = "Next >>", state = 'disabled', command = self.nextImage)
        self.button4.bind_all("s", self.nextImage)
        self.button4.bind_all("d", self.nextImage)
        self.button4.place(x = 90, y = 250, width = 65, height = 20)
        self.button5 = Button(self.frame, text ="Delete Image", state = 'disabled', command = self.Delete_image)
        self.button5.place(x = 170, y = 250, width = 90, height = 20)
        self.button6 = Button(self.frame, text = "Help", command = Help)
        self.button6.place(x = 275, y = 250, width = 65, height = 20)

        # main panel for labeling
        self.canvas_w = self.w - 370    # The size of canvas.
        self.canvas_h = self.h - 80
        self.mainPanel = Canvas(self.frame, bg = 'white')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Button-3>", self.popupList)
        self.mainPanel.bind("<Button-2>", self.delete_line)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.mainPanel.place(x = 360, y = 10, width = self.canvas_w, height = self.canvas_h)

        # showing bbox info & delete bbox
        self.listbox = Listbox(self.frame)
        self.listbox.place(x = 10, y = 120, width = 250, height = 120)
        
        # showing log
        self.label9 = Label(self.frame, text = "Print Log:")
        self.label9.place(x = 1, y = 280, width = 71, height = 20)
        self.messageList = Listbox(self.frame)
        self.messageList.place(x = 10, y = 300, width = 336, height = 300)

        # Right-click menu, display class name.
        self.contextMenu = Menu(self.frame)
        self.Classes = StringVar()
        for classes in CLASSES:
            self.contextMenu.add_radiobutton(label = classes, variable = self.Classes, command = self.clickMenu)

    def Rectangle(self):
        self.flag = 0
        self.button.config(state='active')

    def Polygon(self):
        self.flag = 1
        self.button.config(state='active')

    def Load_image(self):
        filename = filedialog.askdirectory()
        self.imageList = glob.glob(os.path.join(filename, '*.jpg'))
        if len(self.imageList) == 0:
            messagebox.showinfo('Information', 'No .JPEG images found in the specified dir!')
            return

        self.button1.config(state='active')
        self.button2.config(state='active')
        self.button3.config(state='active')
        self.button4.config(state='active')
        self.button5.config(state='active')
        self.cur = 1
        self.total = len(self.imageList)
        self.messageList.insert(END, "The number of images is %d " % self.total)

        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)
        if not os.path.exists('./label'):
            os.mkdir('./label')

        self.loadImage()

    def loadImage(self):
        # load image
        image_path = self.imageList[self.cur - 1]
        entry = StringVar()
        entry.set(image_path)
        self.label2.config(textvariable = entry)
        self.img = Image.open(image_path)
        size_img = np.shape(self.img)
        self.width = size_img[1]
        self.height = size_img[0]
        self.depth = size_img[2]
        self.img = self.img.resize((self.canvas_w, self.canvas_h), Image.ANTIALIAS)
        self.tkimg = ImageTk.PhotoImage(self.img)
        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)
        self.label6.config(text = "Doing: %d/%d" %(self.cur, self.total))
        self.label4.config(text = '(%d, %d, %d)' % (self.width, self.height, self.depth))

        # load labels
        self.clearBBox()
        self.image_name = os.path.split(image_path)[-1].split('.')[0]
        label_name = self.image_name + '.xml'
        self.label_filename = os.path.join(self.outDir, label_name)
        label_name1 = self.image_name + '.txt'
        self.label_filename1 = os.path.join('./label', label_name1)
        if os.path.exists(self.label_filename1):
            with open(self.label_filename1) as f:
                for (ind, line) in enumerate(f):
                    if ind == 0:
                        continue
                    if self.flag == 0:
                        tmp = [t.strip() for t in line.split()]
                        self.bboxList.append(tuple([tmp[0], tmp[1], tmp[2], tmp[3]]))
                        self.classes_name.append(tmp[4])
                        x = float(tmp[0]) * self.canvas_w / self.width
                        y = float(tmp[1]) * self.canvas_h / self.height
                        xx = float(tmp[2]) * self.canvas_w / self.width
                        yy = float(tmp[3]) * self.canvas_h / self.height
                        color = COLORS[(len(self.bboxList) - 1) % len(COLORS)]
                        tmpId = self.mainPanel.create_rectangle(int(x), int(y), int(xx), int(yy), width = 2, outline = color)
                        classId = self.mainPanel.create_text(int(x) + 5, int(y) + 8, text = tmp[4], anchor = W, fill = color)
                        self.bboxIdList.append(tmpId)
                        self.classIdList.append(classId)
                        self.listbox.insert(END, '(%s, %s) -> (%s, %s) -> %s' % (tmp[0], tmp[1], tmp[2], tmp[3], tmp[4]))
                        self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = color)
                    if self.flag == 1:
                        tmp = [t.strip() for t in line.split()]
                        boxes = []
                        self.coordinate = []
                        self.bboxIdLine = []
                        for i in range(0, len(tmp)-1, 2):
                            self.coordinate.append((tmp[i], tmp[i+1]))
                            x = float(tmp[i]) * self.canvas_w / self.width
                            y = float(tmp[i+1]) * self.canvas_h / self.height
                            boxes.append((int(x), int(y)))
                        self.bboxList.append(self.coordinate)
                        self.classes_name.append(tmp[8])
                        color = COLORS[(len(self.bboxList) - 1) % len(COLORS)]
                        classId = self.mainPanel.create_text(boxes[0][0]+5, boxes[0][1]+8, text = tmp[8], anchor = W, fill = color)
                        for i in range(len(boxes)-1):
                            tmpId = self.mainPanel.create_line(boxes[i], boxes[i+1], width = 2, fill = color)
                            self.bboxIdLine.append(tmpId)
                        tmpId = self.mainPanel.create_line(boxes[3], boxes[0], width=2, fill=color)
                        self.bboxIdLine.append(tmpId)
                        self.bboxIdList.append(self.bboxIdLine)
                        self.classIdList.append(classId)
                        self.listbox.insert(END, '(%d,%d)->(%d,%d)->(%d,%d)->(%d,%d)->%s' % (boxes[0][0], boxes[0][1], boxes[1][0], boxes[1][1], boxes[2][0],
                                                                                             boxes[2][1], boxes[3][0], boxes[3][1],self.class_name))
                        self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = color)

    def saveImage(self):
        if self.classes_name:
            img_name = self.image_name + '.jpg'
            shape = [self.width, self.height, self.depth]
            doc = createXML(img_name, shape, self.classes_name, self.bboxList, self.flag)
            writeXMLFile(doc, self.label_filename)

            with open(self.label_filename1, 'w') as f:
                f.write('%d\n' % len(self.bboxList))
                if self.flag == 0:
                    for ind in range(len(self.classes_name)):
                        f.write(' '.join(map(str, self.bboxList[ind])) + ' ' + self.classes_name[ind] + '\n')

                if self.flag == 1:
                    for ind in range(len(self.classes_name)):
                        for box in self.bboxList[ind]:
                            f.write(str(box[0]) + ' ' + str(box[1]) + ' ')
                        f.write(self.classes_name[ind] + '\n')

            self.messageList.insert(END, "Image No. %d saved" % self.cur)
            if len(self.messageList.get(0,END)) > 16:
                self.messageList.delete(1)

    def mouseClick(self, event):
        if self.flag == 0:
            if self.STATE['click'] == 0:
                self.STATE['x'], self.STATE['y'] = event.x, event.y
            else:
                self.x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
                self.y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)
                self.xx1 = int(float(self.x1) * self.width / self.canvas_w)
                self.x2 = int(float(x2) * self.width / self.canvas_w)
                self.yy1 = int(float(self.y1) * self.height / self.canvas_h)
                self.y2 = int(float(y2) * self.height / self.canvas_h)
                self.bboxList.append((self.xx1, self.yy1, self.x2, self.y2))
                self.bboxIdList.append(self.bboxId)
                self.bboxId = None
            self.STATE['click'] = 1 - self.STATE['click']

        if self.flag == 1:
            if self.STATE['click'] == 0:
                self.STATE['x'], self.STATE['y'] = event.x, event.y
                x1, x2 = event.x, event.y
                self.x1, self.y1 = event.x, event.y
            else:
                x1, x2 = event.x, event.y
            x1 = int(float(x1) * self.width / self.canvas_w)
            x2 = int(float(x2) * self.height / self.canvas_h)
            self.STATE['x'], self.STATE['y'] = event.x, event.y
            self.coordinate.append((x1, x2))
            if self.bboxId:
                self.bboxIdLine.append(self.bboxId)
            self.STATE['click'] += 1
            if self.STATE['click'] == 4:
                self.STATE['click'] = 0
                self.bboxList.append(self.coordinate)
                self.bboxId = self.mainPanel.create_line(self.STATE["x"], self.STATE['y'], self.x1, self.y1, width=2,
                                                         fill=self.color_map)
                self.bboxIdLine.append(self.bboxId)
                self.bboxIdList.append(self.bboxIdLine)
                self.coordinate = []
                self.bboxIdLine = []

            self.bboxId = None


    def mouseMove(self, event):
        self.color_map = COLORS[len(self.bboxIdList) % len(COLORS)]
        self.label7.config(text = 'x: %.2f' % event.x)
        self.label8.config(text = 'y: %.2f' % event.y)
        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width = 2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width = 2)
        if self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            if self.flag == 0:
                self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], event.x, event.y, width = 2, outline = self.color_map)
            if self.flag == 1:
                self.bboxId = self.mainPanel.create_line(self.STATE["x"], self.STATE['y'], event.x, event.y, width = 2, fill = self.color_map)

    def popupList(self, event):
        self.contextMenu.post(event.x_root, event.y_root)

    def clickMenu(self):
        self.class_name = self.Classes.get()
        self.color_map = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)]
        if self.flag == 0:
            self.listbox.insert(END, '(%d, %d) -> (%d, %d) -> %s' % (self.xx1, self.yy1, self.x2, self.y2, self.class_name))
        if self.flag == 1:
            num = len(self.bboxIdList)
            coor = self.bboxList[num - 1]
            self.listbox.insert(END, '(%d,%d)->(%d,%d)->(%d,%d)->(%d,%d)->%s' % (coor[0][0], coor[0][1], coor[1][0], coor[1][1],
                                coor[2][0], coor[2][1], coor[3][0], coor[3][1], self.class_name))
        self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = self.color_map)
        classIdx = self.mainPanel.create_text(self.x1+5, self.y1+8, text = self.class_name, anchor = W, fill = self.color_map)
        self.classes_name.append(self.class_name)
        self.classIdList.append(classIdx)

    def delete_line(self, event):
        if self.bboxId:
            try:
                if self.flag == 0:
                    self.mainPanel.delete(self.bboxId)
                    self.bboxId = None
                    self.STATE['click'] = 0
            except:
                pass
        else:
            try:
                if self.flag == 0:
                    if len(self.bboxIdList) != len(self.classes_name):
                        boxId = self.bboxIdList.pop()
                        self.mainPanel.delete(boxId)
                        self.bboxList.pop()
                if self.flag == 1:
                    if len(self.bboxIdList) != len(self.classes_name):
                        boxId = self.bboxIdList.pop()
                        self.bboxList.pop()
                        for Id in boxId:
                            self.mainPanel.delete(Id)
            except:
                pass

    def delBBox(self):
        try:
            sel = self.listbox.curselection()
            if len(sel) != 1 :
                return
            idx = int(sel[0])
            if self.flag == 0:
                self.mainPanel.delete(self.bboxIdList[idx])
            if self.flag == 1:
                for Id in self.bboxIdList[idx]:
                    self.mainPanel.delete(Id)
            self.mainPanel.delete(self.classIdList[idx])
            self.bboxIdList.pop(idx)
            self.classIdList.pop(idx)
            self.bboxList.pop(idx)
            self.classes_name.pop(idx)
            self.listbox.delete(idx)
        except:
            pass

    def clearBBox(self):
        try:
            for idx in range(len(self.bboxIdList)):
                if self.flag == 0:
                    self.mainPanel.delete(self.bboxIdList[idx])
                if self.flag == 1:
                    for Id in self.bboxIdList[idx]:
                        self.mainPanel.delete(Id)
                self.mainPanel.delete(self.classIdList[idx])
            self.listbox.delete(0, len(self.classes_name))
            self.bboxIdList = []
            self.classIdList = []
            self.bboxList = []
            self.classes_name = []
            self.coordinate = []
            self.bboxIdLine = []
        except:
            pass

    def Delete_image(self, event):
        image_path = self.imageList[self.cur-1]
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()
        else:
            self.messageList.insert(END, "Image NO. %d deleted" % self.cur)
            if len(self.messageList.get(0,END)) > 1:
                self.messageList.delete(1)
            messagebox.showinfo('Information','\tCompleted!\n\nAll images have been labelled!')
        os.remove(image_path)
        self.del_num += 1
        self.messageList.insert(END, "Image NO. %d deleted \t%d images have been deleted." %(self.cur-1, self.del_num))
        if len(self.messageList.get(0, END)) > 16:
            self.messageList.delete(1)

    def prevImage(self, event = None):
        try:
            self.saveImage()
            if self.cur > 1:
                self.cur -= 1
                self.loadImage()
            else:
                messagebox.showinfo('Information', "\t\n\nIt's already the first image.")
        except:
            pass

    def nextImage(self, event = None):
        try:
            self.saveImage()
            if self.cur < self.total:
                self.cur += 1
                self.loadImage()
            else:
                self.messageList.insert(END, "All images have been labelled!")
                if len(self.messageList.get(0,END)) > 16:
                    self.messageList.delete(1)
                messagebox.showinfo('Information','\tCompleted!\n\nAll images have been labelled!')
        except:
            pass

def createElementNode(doc, tag, attr):
    element_node = doc.createElement(tag)
    text_node = doc.createTextNode(attr)
    element_node.appendChild(text_node)
    return element_node

def createChildNode(doc, tag, attr, parent_node):
    child_node = createElementNode(doc, tag, attr)
    parent_node.appendChild(child_node)

def createObjectNode(doc, classes_name, bbox, flag):
    object_node = doc.createElement('object')
    for i in range(len(classes_name)):
        class_name = classes_name[i]
        boxes = bbox[i]
        createChildNode(doc, 'name', class_name, object_node)
        createChildNode(doc, 'pose', _POSE, object_node)
        createChildNode(doc, 'truncated', _TRUNCATED, object_node)
        createChildNode(doc, 'difficult', _DIFFICULT, object_node)

        bndbox_node = doc.createElement('bndbox')
        if flag == 0:
            createChildNode(doc, 'xmin', str(boxes[0]), bndbox_node)
            createChildNode(doc, 'ymin', str(boxes[1]), bndbox_node)
            createChildNode(doc, 'xmax', str(boxes[2]), bndbox_node)
            createChildNode(doc, 'ymax', str(boxes[3]), bndbox_node)
        if flag == 1:
            createChildNode(doc, 'xlu', str(boxes[0][0]), bndbox_node)
            createChildNode(doc, 'ylu', str(boxes[0][1]), bndbox_node)
            createChildNode(doc, 'xru', str(boxes[1][0]), bndbox_node)
            createChildNode(doc, 'yru', str(boxes[1][1]), bndbox_node)
            createChildNode(doc, 'xrd', str(boxes[2][0]), bndbox_node)
            createChildNode(doc, 'yrd', str(boxes[2][1]), bndbox_node)
            createChildNode(doc, 'xld', str(boxes[3][0]), bndbox_node)
            createChildNode(doc, 'yld', str(boxes[3][1]), bndbox_node)

        object_node.appendChild(bndbox_node)
    return object_node

def writeXMLFile(doc, filename):
    tmpfile = open('tmp.xml', 'w')
    doc.writexml(tmpfile, addindent = ' '*4, newl = '\n', encoding = 'utf-8')
    tmpfile.close()

    fin = open('tmp.xml')
    fout = open(filename, 'w')
    lines = fin.readlines()

    for line in lines[1:]:
        if line.split():
            fout.writelines(line)
    fin.close()
    fout.close()
    os.remove('tmp.xml')

def createXML(image_name, shape, classes_name, bbox, flag):
    my_dom = xml.dom.getDOMImplementation()
    doc = my_dom.createDocument(None, 'annotation', None)

    root_node = doc.documentElement
    createChildNode(doc, 'folder', 'HUST2018', root_node)
    createChildNode(doc, 'filename', image_name, root_node)

    source_node = doc.createElement('source')
    createChildNode(doc, 'database', 'Detection', source_node)
    createChildNode(doc, 'annotation', 'HUST2018', source_node)
    createChildNode(doc, 'image', 'flickr', source_node)
    createChildNode(doc, 'flickrid', 'NULL', source_node)
    root_node.appendChild(source_node)

    owner_node = doc.createElement('owner')
    createChildNode(doc, 'flickr_url', '0', owner_node)
    createChildNode(doc, 'name', '?', owner_node)
    root_node.appendChild(owner_node)

    size_node = doc.createElement('size')
    createChildNode(doc, 'width', str(shape[0]), size_node)
    createChildNode(doc, 'height', str(shape[1]), size_node)
    createChildNode(doc, 'depth', str(shape[2]), size_node)
    root_node.appendChild(size_node)

    createChildNode(doc, 'segmented', _SEGMENTED, root_node)

    object_node = createObjectNode(doc, classes_name, bbox, flag)
    root_node.appendChild(object_node)
    return doc

def Help():
    space = "     "
    p = "\n\n" + space + "This is a simple tool for labelling object in image.\n"
    p1 = space + "The Label-Tool can label rectangle (two coordinates) and polygon (four coordinates), you can select mode.\n\n"
    p2 = space + "Usage:\n"
    p3 = space + space + "1. Select mode (rectangle or polygon). This is a radio, you can only choose one, and can't change mode during labelling.\n"
    p4 = space + space + "2. Select path that has '.jpg' file. If not '.jpg' format, you can run 'image.py' to generate and number images.\n"
    p5 = space + space + "3. Label:\n"
    p6 = "\tIf you choose 'rectangle', click the left mouse button, select the first point, then move the mouse, click the left button " \
         "again, select the second point, and then you can see the rectangle. And then click the right mouse button to select class name. " \
         "Finally, a bounding box is labelled.\n"
    p7 = "\nNOTE: If you draw rectangle wrong and class name has not been selected, you can click middle mouse button to delete rectangle. " \
         "If class name has been selected, you can click the bounding box that you want to delete in 'Bounding Box', then click 'Delete' " \
         "button. If you want to delete all bounding boxes, you can click 'ClearAll' button.\n\n"
    p8 = "\tIf you choose 'polygon', click the left mouse button four times to select four points, then you can see the polygon. And " \
         "then click the right mouse button to select class name.\n" \
         "\nNOTE: When you label polygon, you must click left-up, right-up, right-down, left-down of the polygon in order.\n\n"
    p9 = space + space + "4. If you label a image, click 'Next >>' button to next image, or you can press shortcut 's' or 'd' to next image. " \
                         "If you want to check previous image, you can click '<< Prev' button, or press shortcut 'w' or 'a'.\n"
    p10 = space + space + "5. If you think the image is not good, you can click 'Delete Image' button to delete image.\n"
    p11 = space + space + "6. Image's label is saved to '.xml' format, this is VOC format, you can easily use. Image's " \
                          "label is also saved to '.txt' format, this is used to check annotation.\n"
    p12 = "\nNOTE: Image shows on the canvas, the image is forced to zoom to the canvas size, so the image may be distorted, but " \
          "this is no problem, the coordinates of the annotation are restored to the original image size.\n"
    p13 = "\nNOTE: If you label your own data set, you need to modify 'CLASSES'.\n"
    p14 = "\nNOTE: If you find a bug in using, you can submit it in the issue."
    log = p + p1 + p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9 + p10 + p11 + p12 + p13 + p14
    messagebox.showinfo('Help', log)

if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.mainloop()
