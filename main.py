#-------------------------------------------------------------------------------
# Name:        Object bounding box label tool
# Purpose:     Label object bboxes for ImageNet Detection data
# Author:      HUST
# Created:     27/07/2017
#
#-------------------------------------------------------------------------------
from __future__ import division
from tkinter import *
from tkinter import messagebox, ttk, filedialog
# from tkinter import ttk
import numpy as np
from PIL import Image, ImageTk
import os
import glob

# colors for the bboxes
COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']
CLASSES = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']
# image sizes for the examples
SIZE = 256, 256


def eventhandler(event):
    pass

class LabelTool():
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("LabelTool")
        self.w, self.h =  self.parent.maxsize()
        #self.parent.geometry('%dx%d' %(w, h))
        self.parent.state('zoomed')
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        #self.parent.resizable(width = 1360, height = 768)

        # initialize global state
        self.imageDir = ''
        self.imageList= []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = 0
        self.del_num = 0
        self.imagename = ''
        self.labelfilename = ''
        self.labelfilename1 = ''
        self.tkimg = None

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.class_name = None
        self.classes_name = []
        self.bboxIdList = []
        self.classIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        radvar = IntVar()
        self.label = Label(self.frame, text = 'Label Type:')
        self.label.place(x = 10, y = 10, width = 70, height = 16)
        self.rad = Radiobutton(self.frame, text = 'rectangle', variable = radvar, value = 1, command = None)
        self.rad.place(x = 90, y = 10, width = 80, height = 16)
        self.rad1 = Radiobutton(self.frame, text = 'line', variable = radvar, value = 2, command = None)
        self.rad1.place(x = 180, y = 10, width = 80, height = 16)

        self.label1 = Label(self.frame, text = 'Image Path:')
        self.label1.place(x = 10, y = 40, width = 71, height = 16)
        self.label2 = Entry(self.frame)
        self.label2.place(x=90, y=40, width=255, height=20)
        self.label3 = Label(self.frame, text = 'Image Size:')
        self.label3.place(x = 10, y = 70, width = 71, height = 16)
        self.label4 = Label(self.frame, bg='white')
        self.label4.place(x=90, y=70, width=171, height=20)
        self.label5 = Label(self.frame, text = 'Bounding Box:')
        self.label5.place(x = 3, y = 100, width = 101, height = 16)
        self.label6 = Label(self.frame, text="Doing:     /    ")
        self.label6.place(x = 120, y = 100 , width = 150, height = 16)
        self.label7 = Label(self.frame, bg = 'white', fg = 'red', anchor = W, text = 'x: ')
        self.label7.place(x = 270, y = 120, width = 75, height = 20)
        self.label8 = Label(self.frame, bg='white', fg='red', anchor=W, text='y: ')
        self.label8.place(x=270, y=145, width=75, height=20)

        self.button = Button(self.frame, text = "Load Image", state = 'disabled', command = self.Load_image)
        self.button.place(x=270, y=70, width=75, height=20)
        self.button.config(state = 'active')
        self.button1 = Button(self.frame, text='Delete', state = 'disabled', command=self.delBBox)
        self.button1.place(x = 270, y = 190, width = 75, height = 20)
        self.button1.config(state='active')
        self.button2 = Button(self.frame, text='ClearAll', state = 'disabled', command=self.clearBBox)
        self.button2.place(x  =270, y = 220, width = 75, height = 20)
        self.button2.config(state='active')
        self.button3 = Button(self.frame, text='<< Prev', state = 'disabled', command=self.prevImage)
        self.button3.bind('w', eventhandler)
        self.button3.place(x = 10, y = 250, width = 65, height = 20)
        self.button3.config(state='active')
        self.button4 = Button(self.frame, text='Next >>', state = 'disabled', command=self.nextImage)
        self.button4.bind_all('s', eventhandler)
        self.button4.config(state='active')
        self.button4.place(x = 90, y = 250, width = 65, height = 20)
        self.button5 = Button(self.frame, text="Delete Image", state = 'disabled', command=self.Delete_image)
        self.button5.place(x = 170, y = 250, width = 90, height = 20)
        self.button6 = Button(self.frame, text="Help", command=None)
        self.button6.place(x=275, y=250, width=65, height=20)

        # main panel for labeling
        self.canvas_w = self.w - 370
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

        self.contextMenu = Menu(self.frame)
        self.Classes = StringVar()
        for classes in CLASSES:
            self.contextMenu.add_radiobutton(label = classes, variable = self.Classes, command = self.clickMenu)#variable = classes,

        # self.tmpLabel = Label(self.frame, text="Go to Image No.")
        # self.idxEntry = Entry(self.frame, width=1)
        # self.goBtn = Button(self.frame, text='Go', command=self.gotoImage)

        #self.frame.columnconfigure(1, weight = 1)
        #self.frame.rowconfigure(2, weight = 1)

    def Load_image(self):
        filename = filedialog.askdirectory()
        self.imageList = glob.glob(os.path.join(filename, '*.jpg'))
        if len(self.imageList) == 0:
            messagebox.showinfo('Information', 'No .JPEG images found in the specified dir!')
            return

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)
        print('The number of images is %d ' % self.total)

        self.outDir = './Labels'
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)
        if not os.path.exists('./label'):
            os.mkdir('./label')

        self.loadImage()

    def loadImage(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        entry = StringVar()
        entry.set(imagepath)
        self.label2.config(textvariable = entry)
        self.img = Image.open(imagepath)
        size_img = np.shape(self.img)
        self.width = size_img[1]
        self.height = size_img[0]
        self.depth = size_img[2]
        self.img = self.img.resize((self.canvas_w, self.canvas_h), Image.ANTIALIAS)
        self.tkimg = ImageTk.PhotoImage(self.img)
        # self.mainPanel.config(width = max(self.tkimg.width(), 400), height = max(self.tkimg.height(), 400))
        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)
        self.label6.config(text = "Doing: %d/%d" %(self.cur, self.total))
        self.label4.config(text = '(%d, %d, %d)' % (self.width, self.height, self.depth))

        # load labels
        self.clearBBox()
        self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        labelname = self.imagename + '.xml'
        self.labelfilename = os.path.join(self.outDir, labelname)
        labelname1 = self.imagename + '.txt'
        self.labelfilename1 = os.path.join('./label', labelname1)
        if os.path.exists(self.labelfilename1):
            self.classes_name = []
            with open(self.labelfilename1) as f:
                for (i, line) in enumerate(f):
                    if i == 0:
                        continue
                    tmp = [t.strip() for t in line.split()]
                    self.bboxList.append(tuple([int(tmp[0]), int(tmp[1]), int(tmp[2]), int(tmp[3])]))
                    self.classes_name.append(tmp[4])
                    tmpId = self.mainPanel.create_rectangle(int(tmp[0]), int(tmp[1]), int(tmp[2]), int(tmp[3]), width = 2,
                                                            outline = COLORS[(len(self.bboxList)-1) % len(COLORS)])
                    classId = self.mainPanel.create_text(int(tmp[0])+5, int(tmp[1])+8, text = tmp[4], anchor = W, fill = COLORS[(len(self.bboxList)-1) % len(COLORS)])
                    self.bboxIdList.append(tmpId)
                    self.classIdList.append(classId)
                    self.listbox.insert(END, '(%s, %s) -> (%s, %s) -> %s' %(tmp[0], tmp[1], tmp[2], tmp[3], tmp[4]))
                    self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])

    def saveImage(self):
        if self.classes_name:
            size_img = np.shape(self.img)
            width = size_img[1]
            height = size_img[0]
            depth = size_img[2]
            with open(self.labelfilename, 'w') as f:
                f.write('<annotation>\n\t<folder>VOC2007</folder>\n\t<filename>%s</filename>\n<source>\n\t\t<database>The VOC2007 Database</database>\n\t\t'
                        '<annotation>PASCAL VOC2007</annotation>\n\t\t<image>flickr</image>\n\t\t<flickrid>325991873</flickrid>\n\t</source>\n\t'
                        '<owner>\n\t\t<flickrid>archintent louisville</flickrid>\n\t\t<name>?</name>\n\t</owner>\n\t<size>\n\t\t<width>%d</width>\n\t\t'
                        '<height>%d</height>\n\t\t<depth>%d</depth>\n\t</size>\n\t<segmented>0</segmented>\n' %(self.imagename+'.jpg', width, height, depth))

                for i in range(0, len(self.bboxList)):
                    f.write('\t<object>\n\t\t<name>%s</name>\n\t\t<pose>?</pose>\n\t\t<truncated>0</truncated>\n\t\t<difficult>0</difficult>\n\t\t<bndbox>'
                            '\n\t\t\t<xmin>%d</xmin>\n\t\t\t<ymin>%d</ymin>\n\t\t\t<xmax>%d</xmax>\n\t\t\t<ymax>%d</ymax>\n\t\t</bndbox>\n\t</object>\n'
                            %(self.classes_name[i], self.bboxList[i][0], self.bboxList[i][1], self.bboxList[i][2], self.bboxList[i][3]))
                f.write('</annotation>')

            with open(self.labelfilename1, 'w') as f:
                num = 0
                f.write('%d\n' % len(self.bboxList))
                for bbox in self.bboxList:
                    f.write(' '.join(map(str, bbox)) + ' ' + self.classes_name[num] + '\n')
                    num += 1

            print('Image No. %d saved' % self.cur)

    def mouseClick(self, event):
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y
        else:
            self.x1, self.x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            self.y1, self.y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)
            self.bboxList.append((self.x1, self.y1, self.x2, self.y2))
            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            # self.listbox.insert(END, '(%d, %d) -> (%d, %d)' %(self.x1, self.y1, self.x2, self.y2))
            # self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
        self.STATE['click'] = 1 - self.STATE['click']


    def mouseMove(self, event):
        self.label7.config(text = 'x: %.2f' % event.x)
        self.label8.config(text = 'y: %.2f' % event.y)
        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width = 2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width = 2)
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], event.x, event.y,
                                                            width = 2, outline = COLORS[len(self.bboxList) % len(COLORS)])

    def popupList(self, event):
        self.contextMenu.post(event.x_root, event.y_root)

    def clickMenu(self):
        self.class_name = self.Classes.get()
        self.listbox.insert(END, '(%d, %d) -> (%d, %d) -> %s' % (self.x1, self.y1, self.x2, self.y2, self.class_name))
        self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
        classIdx = self.mainPanel.create_text(self.x1+5, self.y1+8, text = self.class_name, anchor = W, fill = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
        self.classes_name.append(self.class_name)
        self.classIdList.append(classIdx)

    def delete_line(self, event):
        try:
            self.mainPanel.delete(self.bboxId)
            self.bboxId = None
            self.STATE['click'] = 0
        except:
            pass

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.bboxIdList[idx])
        self.mainPanel.delete(self.classIdList[idx])
        self.bboxIdList.pop(idx)
        self.classIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
            self.mainPanel.delete(self.classIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.classIdList = []
        self.bboxList = []
        self.classes_name = []

    def Delete_image(self, event):
        imagepath = self.imageList[self.cur-1]
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()
        else:
            print("Image NO. %d deleted" % self.cur)
            messagebox.showinfo('Information','\tCompleted!\n\nAll images have been labelled!')
        os.remove(imagepath)
        self.del_num += 1
        print("Image NO. %d deleted \t%d images have been deleted." %(self.cur-1, self.del_num))

    def prevImage(self, event = None):
        self.saveImage()
        self.classes_name = []
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()

    def nextImage(self, event = None):
        self.saveImage()
        self.classes_name = []
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()
        else:
            messagebox.showinfo('Information','\tCompleted!\n\nAll images have been labelled!')

    # def gotoImage(self):
    #     idx = int(self.idxEntry.get())
    #     if 1 <= idx <= self.total:
    #         self.saveImage()
    #         self.cur = idx
    #         self.loadImage()


if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.mainloop()
