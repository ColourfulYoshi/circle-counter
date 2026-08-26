# circle-counter
Nine Circles

circle-counter (Nine Circles, NC or CC) is a small utility made for detecting white circles, and then additionally approximating the amount in an area with an even density.

# requirements
all specified in the `requirements.txt` file

# usage
<img width="852" height="732" alt="main interface" src="https://github.com/user-attachments/assets/8b10a46f-8726-462f-a416-6eb90707d586" />

open an image, select an area using the "Area" button, which will prompt you to click to select a rectangular area. afterwards press "Detect" and all circles will be highlighted according to the Detection Config.
### approximate result:
<img width="852" height="732" alt="result" src="https://github.com/user-attachments/assets/874327ec-875c-46a8-9159-4dc1d5866a11" />
### original image used:
<img width="460" height="437" alt="testimg_1" src="https://github.com/user-attachments/assets/c6893360-32d3-4158-90e3-6a2b980f8474" />

the amount of circles will be shown in the canvas at the bottom, along with the approximated number on the entire field. detected circles are highlighted on the image itself too. 

**note: resizing the window resets the area.**

for fine-tuning, and proper usage, read the interface documentation below.

# documentation: main interface

## Image
<img width="143" height="96" alt="image" src="https://github.com/user-attachments/assets/2233bd81-2b93-498e-ba73-9f535613c98c" />

* `Open` - opens a file dialog to select an image to be loaded. supports _.png_, _.jpg_ and _.jpeg_ files. other files can be selected, but not recommended.
* `Paste` - paste an image from the buffer.
* `Clear` - clears the image and all points placed.
* the "0x0" label is for the image dimensions of a selected file.

## Detection Config
<img width="143" height="337" alt="config" src="https://github.com/user-attachments/assets/c7d0691a-fd85-4144-aed6-f6fe4fbbbd0a" />

* `min_area`/`max_area` [positive int] - the minimum and maximum pixel areas of the circle when the image is converted and processed. this will be scaled with `base area` and `base ratio`.
* `base area`/`base ratio` [positive float] - used for scaling the minimum and maximum areas along with image dimensions. this can be disabled if you input "0" for `base area`.
* `min thresh`/`max thresh` [positive int] - the minimum and maximum range for the grayscale value of the circles. you can use the colorpicker button nearby to select the value from the image itself.
* `glare val`/`glare max` [positive int] - if `filter glare` is enabled, will filter out the area that has that grayscale color in range before detection.
* `prop size` [positive float] - the size of the **entire field** on one axis, basically everything that is outside the frame. used in the final approximation.
* `area size` [positive float] - the size of the **selected area** on one axis, and only the selected area. used in the final approximation.
* `blur ksize` [positive odd int] - ksize of the gaussian blur before the detection, to filter out noise or merge noisy areas.
* `glare blur` [positive int] - if `filter glare` is enabled, this is the coefficent used to blur the image before filtering out glare.

## main buttons
<img width="136" height="102" alt="buttons" src="https://github.com/user-attachments/assets/5de8910f-ac48-4dd6-a91e-b935c4fd4cc9" />

* `Area` - prompts you to click on the points on the image to select an area, or cancel selecting an area you're currently placing.
* `Clear` - clears the area.
* `Type:` - area type:
  * `4 points` - click on 4 different spots on the image to place the points. after all 4 are placed, the final area will be selected.
  * `8 points` - similiarly to 4 points, however requires you to place 8 points instead.
  * `square` - click on the first point of the area you want to select. now, hold right click and release it at the end point. this will create a rectangular area.
* `Detect` - runs the detection command with the Detection Config.

## checkbuttons
<img width="227" height="89" alt="checkbuttons" src="https://github.com/user-attachments/assets/10f6bb72-2df4-41ee-bfd4-abb09b6d062f" />

* `debug images` - after the detection command is ran, if this is enabled, will also open separate windows of image masks for debugging.
* `filter glare` - whether to run the glare filter algorithm or not.
* `glare range` - whether all grayscale values in-between `glare val` and `glare max` should be ignored. needs to have `filter glare` enabled.
* `glare fill` - determines how glare will be filtered out. having this on will do `cv2.inpaint` on the filtered spots, otherwise will simply replace all the spots with black pixels.
* `RGB to BGR` - before detection, whether to change the color format of the image from RGB to BGR. affects the grayscale values.
* `glare HSV mask` - if this is on, the glare filter mask will be in the HSV format, and `glare val` and `glare max` will check the value of the pixels. if this is off, the mask will be grayscale. has no effect if `filter glare` is off.
* `clear cv2 windows` - when pressed, will destroy all cv2 (debug) windows. after that it will switch itself back to the off state.

# documentation: topbar

## File
<img width="93" height="92" alt="file topbar" src="https://github.com/user-attachments/assets/e2476591-5d0e-443e-8992-efbe69cbc255" />

exact same functionality as the Image section, however "Clear" is renamed to "Close" here.

## Theme
<img width="97" height="246" alt="theme topbar" src="https://github.com/user-attachments/assets/701e8b4c-b75d-43cc-a161-ee97df44ceb3" />

theme selection menu. `[Advanced]` opens the Theme Select menu, all options below are the available themes.

## Settings
<img width="97" height="90" alt="settings topbar" src="https://github.com/user-attachments/assets/278e8fcf-398c-46c7-9b46-9c22fda40099" />

settings dropdown menu.
* `Formula` - opens the Formula Editor menu. see more below.
* `Binders` - opens the Binders menu. see more below.
* `Reset Window` - reset window dimensions to their default.

# documentation: Theme Select
<img width="702" height="382" alt="theme menu" src="https://github.com/user-attachments/assets/f120f88b-15cc-4183-9c63-fe3ba17cd271" />

theme selection and color preview menu. select a category (top), which will have a collection of themes.

# notice
this project is not maintained and was not made for general usage. the repository is made for archiving purposes.

however, code is free to be used and modified.
