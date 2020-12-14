# Copyright(c)2020 by Yangwoo Kim
# ywkim@sju.ac.kr
# https://dms.sejong.ac.kr
import tkinter as tk
import tkinter.ttk
from functools import partial
from tkinter import filedialog
import tkinter.messagebox

import os

# pip install Image
from PIL import ImageTk
from PIL import Image

import struct

#pip install numpy
import numpy as np

IMAGE_FORMAT = ['.png', '.jpg', '.bmp']
RESOLUTION_DIC = {'512x512':(512, 512),'HD':(1280, 720),
                  'FHD':(1920, 1080), 'UHD':(3840, 2160)}
COLOR_SPACE = ['YCbCr', 'RGB']
SUBSAMPLING = ['4:4:4', '4:2:0', '4:0:0']
BITDEPTH = ['8', '10', '16']

tkimage = [None, None, "Image Viewer (DMS LAB)"]




class RootWindows(object):
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Image Viewer (DMS LAB)")
        self.window.geometry("200x200")
        self.window.resizable(False, False)
        self.menubar = tk.Menu(self.window)
        self.label = tk.Label(self.window)
        self.label.pack()
        self.addMenu([('Open', self.FileOpen), ('Save', self.FileSave), ('Save raw', self.FileSaveAsYUV), None, ('Info', self.Info)], name='File')
        self.addMenu([('Down-Sampling', self.DownSampling), ('Up-Sampling', self.UpSampling), None,('GrayScale', self.toGray)], name='Resize')
        self.window.config(menu=self.menubar)
        self.window.mainloop()



    def addMenu(self, menulist, name):
        newmenu = tk.Menu(self.menubar, tearoff=0)
        for submenu in menulist:
            if submenu is None:
                newmenu.add_separator()
            else:
                newmenu.add_command(label=submenu[0], command=partial(submenu[1]))
        self.menubar.add_cascade(label=name, menu=newmenu)

    def FileSave(self):
        ftypes = [('img file', '.png'), ('img file', '.jpg'),('img file', '.bmp')]
        if tkimage[1] is not None:
            filename = os.path.splitext(os.path.basename(tkimage[2]))[0]
            path = filedialog.asksaveasfilename(filetypes=ftypes, title='Save Image',
                                                initialfile='{}.png'.format(filename))
            if not path:
                return
            tkimage[1].convert('RGBA').save(path)

    def FileSaveAsYUV(self):
        ftypes = [('YUV file', '.yuv'), ('All file', '*')]
        if tkimage[1] is not None:
            if tkimage[1].mode=='L':
                ext = 'rgb'
                format = '400'
            else:
                ext = 'yuv'
                format = '444'
            path = filedialog.asksaveasfilename(filetypes=ftypes, title='Save Image',
                                                initialfile='{}_{}x{}_P{}.{}'.format(os.path.splitext(os.path.basename(tkimage[2]))[0],
                                                                                     *tkimage[1].size, format, ext))
            if not path:
                return
            if tkimage[1].mode=='L':
                np.array(tkimage[1]).flatten().tofile(path)
            else:
                np.array(tkimage[1].convert('YCbCr')).transpose((2, 0, 1)).flatten().tofile(path)
            # bin = struct.pack('<' + str(img.size) + 'B', *img)
            # with open(path, 'wb') as f:
            #     f.write(bin)


    def Info(self):
        tkinter.messagebox.showinfo('Information', 'Made By Yangwoo-Kim\nywkim@sju.ac.kr\nDMS LAB\nhttp://dms.sejong.ac.kr/')

    def DownSampling(self):
        if tkimage[1] is not None:
            height, width = tkimage[1].size
            img = tkimage[1].resize((height // 2, width // 2))
            self.renewImage(img, img.size)

    def UpSampling(self):
        if tkimage[1] is not None:
            height, width = tkimage[1].size
            img = tkimage[1].resize((height*2, width*2))
            self.renewImage(img, img.size)

    def toGray(self):
        if tkimage[1] is not None:
            self.renewImage(tkimage[1].convert('L'), tkimage[1].size)


    def UnpackRawImage(self, subsampling, width, height, filename, bitdepth):
        def UpSamplingChroma(UVPic):
            return UVPic.repeat(2, axis=0).repeat(2, axis=1)
        area = width * height
        if subsampling=='444':
            channel = 3
            carea = area
        elif subsampling=='420':
            if height % 2 == 1 or width % 2 == 1:
                return None
            channel = 1.5
            carea = area//4
        else:
            channel = 1
            carea = 0
        pelCumsum = np.cumsum(np.array([area, carea]), dtype='int32')
        pixel_num = int(channel * height * width)
        if bitdepth==8:
            bitdepth_char = 'B'
            dtype = 'uint8'
            bit_mul = 1
        else:
            bitdepth_char = 'h'
            dtype = 'int16'
            bit_mul = 2

        with open(filename, 'rb') as f:
            img = np.array(struct.unpack(str(pixel_num)+ bitdepth_char, f.read(pixel_num * bit_mul)), dtype=dtype)
        if bitdepth!=8:
            img = (img >> (bitdepth - 8)).astype('uint8')
        C1, C2, C3 = np.split(img, pelCumsum)
        if subsampling=='444':
            return np.stack((C1.reshape(height, width),
                                   C2.reshape(height, width),
                                   C3.reshape(height, width)), axis=2)
        elif subsampling=='420':
            cheight = height//2
            cwidth = width//2
            return np.stack((C1.reshape(height, width),
                            UpSamplingChroma(C2.reshape(cheight, cwidth)),
                            UpSamplingChroma(C3.reshape(cheight, cwidth))), axis=2)
        else:
            return C1.reshape(height, width)



    def renewImage(self, img, size=None, filename=None):
        tmp = tkimage[0]
        tkimage[0] = ImageTk.PhotoImage(img, master=self.window)
        try:
            width, height = img.size
            self.window.geometry('{}x{}'.format(width, height))
            if size is None:
                self.window.title("{}_{}x{}".format(filename, width, height))
                tkimage[2] = filename
            else:
                self.window.title("{}_{}x{}".format(tkimage[2], size[0], size[1]))
            self.label.config(image=tkimage[0])
            self.window.update_idletasks()
            tkimage[1] = img
        except Exception as e:
            print(e)
            tkimage[0] = tmp
            self.window.title("Image Viewer (DMS LAB)")

    def FileOpen(self):
        filepath = filedialog.askopenfilename()
        if not len(filepath):
            return
        if os.path.splitext(filepath)[1].lower() in IMAGE_FORMAT:
            img = Image.open(filepath)
            self.renewImage(img, filename=filepath)
        else:
            def size_combo_select():
                if select_size.get() not in RESOLUTION_DIC:
                    return
                width, height = RESOLUTION_DIC[select_size.get()]
                labels[1].delete(0, 100)
                labels[1].insert(0, str(width))
                labels[3].delete(0, 100)
                labels[3].insert(0, str(height))

            def DoneButtonEvent():
                width = labels[1].get()
                height = labels[3].get()
                color = select_color.get()
                sampling = select_sampling.get()
                bitdepth = select_bitdepth.get()
                if color not in COLOR_SPACE or sampling not in SUBSAMPLING:
                    tmp_window.destroy()
                    return
                try:
                    width = int(width)
                    height = int(height)
                    bitdepth = int(bitdepth)
                    sampling = sampling.replace(':', '')
                    img_np_array = self.UnpackRawImage(sampling, width, height, filepath, bitdepth)
                    if sampling == '400':
                        color = 'L'
                    # img_np_array.transpose((2,0,1)).flatten().tofile('C:\\Users\\YangwooKim\\Desktop\\image.yuv')
                    img = Image.fromarray(img_np_array, color)
                    self.renewImage(img, filename=filepath)
                except Exception as e:
                    print(e)
                tmp_window.destroy()

            tmp_window = tk.Toplevel(self.window)
            tmp_window.title('Image Format')
            tmp_window.geometry('300x220')
            tmp_window.resizable(False, False)
            img_size = tk.LabelFrame(tmp_window, text='Image size', pady=10, padx=5)
            tk.Label(img_size, text=' Resolution:   ').grid(row=0, column=0)
            select_size = tkinter.ttk.Combobox(img_size, height=15, width=10, values=list(RESOLUTION_DIC.keys()),
                                               postcommand=size_combo_select)
            select_size.grid(row=0, column=1)
            select_size.set('Choose One')
            labels = [tk.Label(img_size, text='Size (WxH):'), tk.Entry(img_size, width=10),
                      tk.Label(img_size, text='x '), tk.Entry(img_size, width=10), tk.Label(img_size, text='   ')]
            img_size.pack()
            for i, label in enumerate(labels):
                label.grid(row=1, column=i)

            img_format = tk.LabelFrame(tmp_window, text='Image Format', pady=10, padx=5)
            tk.Label(img_format, text=' Color Space:   ').grid(row=0, column=0)
            select_color = tkinter.ttk.Combobox(img_format, height=15, width=10, values=COLOR_SPACE)
            select_color.grid(row=0, column=1)
            select_color.set(COLOR_SPACE[0])
            tk.Label(img_format, text='                       ').grid(row=0, column=3)
            tk.Label(img_format, text=' Subsampling:   ').grid(row=1, column=0)
            select_sampling = tkinter.ttk.Combobox(img_format, height=15, width=10, values=SUBSAMPLING)
            select_sampling.grid(row=1, column=1)
            select_sampling.set(SUBSAMPLING[-1])

            tk.Label(img_format, text=' Bit Depth:   ').grid(row=2, column=0)
            select_bitdepth = tkinter.ttk.Combobox(img_format, height=15, width=10, values=BITDEPTH)
            select_bitdepth.grid(row=2, column=1)
            select_bitdepth.set(BITDEPTH[0])

            img_format.pack()
            button = tk.Button(tmp_window, overrelief="solid", width=15, text='OK', command=DoneButtonEvent,
                               repeatdelay=1000, repeatinterval=100)
            button.pack(side='bottom')
        return


if __name__=='__main__':
    r = RootWindows()