"""A file to calculate the pose transformation between a camera and robot and
a tool offset from correspondences.
"""

# The MIT License (MIT)
#
# Copyright (c) 2016 GTRC.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import argparse
import json

import datetime
import os

import numpy as np

import cv2

from quaternions import Quaternion
from dual_quaternions import DualQuaternion


def main():
    """
    Exposes :py:func:`compute_transformation` to the commandline. Run with arg
    `-h` for more info.
    """
    # Parse in arguments
    parser = argparse.ArgumentParser(
        description="Compute transformation between camera and robot given "
                    "existing correspondences")

    parser.add_argument("--correspondences", type=str,
                        help='The filename for the file containing the list of'
                             'correspondences, which is generated by'
                             'get_correspondences.py. '
                             'Defaults to: correspondences.json',
                        default="correspondences.json")

    parser.add_argument("--out", type=str,
                        help="File to save output to",
                        default="transformation.json")

    args = parser.parse_args()

    compute_transformation(
        correspondences=args.correspondences,
        file_out=args.out
    )


def compute_transformation(correspondences, file_out):
    with open(correspondences, 'r') as correspondences_file:
        correspondences_dictionary = json.load(correspondences_file)
        write_time = correspondences_dictionary['time']
        tcp2robot = correspondences_dictionary['tcp2robot']
        camera2grid = correspondences_dictionary['camera2grid']
        print("Loaded data from {}".format(write_time))

    data = np.zeros((len(tcp2robot)*8, 16))
    for i in range(0, len(tcp2robot)):
        c_raw = camera2grid[i]
        (c_rot_mat, _) = cv2.Rodrigues(np.array(c_raw[3:])) #Calculate rotation matrix from rodrigues values
        c_rot_quat = Quaternion.from_matrix(c_rot_mat)
        c_trans_quat = Quaternion.from_translation(c_raw[:3])
        c = DualQuaternion(c_rot_quat, c_trans_quat)

        t_raw = tcp2robot[i]
        t_rot = Quaternion.from_euler(t_raw[3:])
        t_trans = Quaternion.from_translation(t_raw[:3])
        t = DualQuaternion(t_rot, t_trans)
        t = t.conjugate_reverse()

        data[i*8: (i+1)*8] = np.array([
            [c.real.w*t.real.w+c.real.x*t.real.x+c.real.y*t.real.y+c.real.z*t.real.z,
            -c.real.x*t.real.w+c.real.w*t.real.x+c.real.z*t.real.y-c.real.y*t.real.z,
            -c.real.y*t.real.w-c.real.z*t.real.x+c.real.w*t.real.y+c.real.x*t.real.z,
            -c.real.z*t.real.w+c.real.y*t.real.x-c.real.x*t.real.y+c.real.w*t.real.z,
            0,0,0,0,-1,0,0,0,0,0,0,0],
            [-c.real.z*t.real.w+c.real.y*t.real.x+c.real.x*t.real.y-c.real.w*t.real.z,
            c.real.y*t.real.w+c.real.z*t.real.x+c.real.w*t.real.y+c.real.x*t.real.z,
            c.real.x*t.real.w-c.real.w*t.real.x+c.real.z*t.real.y-c.real.y*t.real.z,
            c.real.w*t.real.w+c.real.x*t.real.x-c.real.y*t.real.y-c.real.z*t.real.z,
            0,0,0,0,0,-1,0,0,0,0,0,0],
            [c.real.y*t.real.w-c.real.z*t.real.x-c.real.w*t.real.y+c.real.x*t.real.z,
            c.real.z*t.real.w+c.real.y*t.real.x+c.real.x*t.real.y+c.real.w*t.real.z,
            c.real.w*t.real.w-c.real.x*t.real.x+c.real.y*t.real.y-c.real.z*t.real.z,
            -c.real.x*t.real.w-c.real.w*t.real.x+c.real.z*t.real.y+c.real.y*t.real.z,
            0,0,0,0,0,0,-1,0,0,0,0,0],
            [c.real.z*t.real.w+c.real.y*t.real.x-c.real.x*t.real.y-c.real.w*t.real.z,
            -c.real.y*t.real.w+c.real.z*t.real.x-c.real.w*t.real.y+c.real.x*t.real.z,
            c.real.x*t.real.w+c.real.w*t.real.x+c.real.z*t.real.y+c.real.y*t.real.z,
            c.real.w*t.real.w-c.real.x*t.real.x-c.real.y*t.real.y+c.real.z*t.real.z,
            0,0,0,0,0,0,0,-1,0,0,0,0],
            [c.real.w*t.dual.w+c.real.x*t.dual.x+c.real.y*t.dual.y+c.real.z*t.dual.z+
                c.dual.w*t.real.w+c.dual.x*t.real.x+c.dual.y*t.real.y+c.dual.z*t.real.z,
            -c.real.x*t.dual.w+c.real.w*t.dual.x+c.real.z*t.dual.y-c.real.y*t.dual.z-
                c.dual.x*t.real.w+c.dual.w*t.real.x+c.dual.z*t.real.y-c.dual.y*t.real.z,
            -c.real.y*t.dual.w-c.real.z*t.dual.x+c.real.w*t.dual.y+c.real.x*t.dual.z-
                c.dual.y*t.real.w-c.dual.z*t.real.x+c.dual.w*t.real.y+c.dual.x*t.real.z,
            -c.real.z*t.dual.w+c.real.y*t.dual.x-c.real.x*t.dual.y+c.real.w*t.dual.z-
                c.dual.z*t.real.w+c.dual.y*t.real.x-c.dual.x*t.real.y+c.dual.w*t.real.z,
            c.real.w*t.real.w+c.real.x*t.real.x+c.real.y*t.real.y+c.real.z*t.real.z,
            -c.real.x*t.real.w+c.real.w*t.real.x+c.real.z*t.real.y-c.real.y*t.real.z,
            -c.real.y*t.real.w-c.real.z*t.real.x+c.real.w*t.real.y+c.real.x*t.real.z,
            -c.real.z*t.real.w+c.real.y*t.real.x-c.real.x*t.real.y+c.real.w*t.real.z,
            0,0,0,0,-1,0,0,0],
            [c.real.x*t.dual.w-c.real.w*t.dual.x+c.real.z*t.dual.y-c.real.y*t.dual.z+
                c.dual.x*t.real.w-c.dual.w*t.real.x+c.dual.z*t.real.y-c.dual.y*t.real.z,
            c.real.w*t.dual.w+c.real.x*t.dual.x-c.real.y*t.dual.y-c.real.z*t.dual.z+
                c.dual.w*t.real.w+c.dual.x*t.real.x-c.dual.y*t.real.y-c.dual.z*t.real.z,
            -c.real.z*t.dual.w+c.real.y*t.dual.x+c.real.x*t.dual.y-c.real.w*t.dual.z-
                c.dual.z*t.real.w+c.dual.y*t.real.x+c.dual.x*t.real.y-c.dual.w*t.real.z,
            c.real.y*t.dual.w+c.real.z*t.dual.x+c.real.w*t.dual.y+c.real.x*t.dual.z+
                c.dual.y*t.real.w+c.dual.z*t.real.x+c.dual.w*t.real.y+c.dual.x*t.real.z,
            c.real.x*t.real.w-c.real.w*t.real.x+c.real.z*t.real.y-c.real.y*t.real.z,
            c.real.w*t.real.w+c.real.x*t.real.x-c.real.y*t.real.y-c.real.z*t.real.z,
            -c.real.z*t.real.w+c.real.y*t.real.x+c.real.x*t.real.y-c.real.w*t.real.z,
            c.real.y*t.real.w+c.real.z*t.real.x+c.real.w*t.real.y+c.real.x*t.real.z,
            0,0,0,0,0,-1,0,0],
            [c.real.y*t.dual.w-c.real.z*t.dual.x-c.real.w*t.dual.y+c.real.x*t.dual.z+
                c.dual.y*t.real.w-c.dual.z*t.real.x-c.dual.w*t.real.y+c.dual.x*t.real.z,
            c.real.z*t.dual.w+c.real.y*t.dual.x+c.real.x*t.dual.y+c.real.w*t.dual.z+
                c.dual.z*t.real.w+c.dual.y*t.real.x+c.dual.x*t.real.y+c.dual.w*t.real.z,
            c.real.w*t.dual.w-c.real.x*t.dual.x+c.real.y*t.dual.y-c.real.z*t.dual.z+
                c.dual.w*t.real.w-c.dual.x*t.real.x+c.dual.y*t.real.y-c.dual.z*t.real.z,
            -c.real.x*t.dual.w-c.real.w*t.dual.x+c.real.z*t.dual.y+c.real.y*t.dual.z-
                c.dual.x*t.real.w-c.dual.w*t.real.x+c.dual.z*t.real.y+c.dual.y*t.real.z,
            c.real.y*t.real.w-c.real.z*t.real.x-c.real.w*t.real.y+c.real.x*t.real.z,
            c.real.z*t.real.w+c.real.y*t.real.x+c.real.x*t.real.y+c.real.w*t.real.z,
            c.real.w*t.real.w-c.real.x*t.real.x+c.real.y*t.real.y-c.real.z*t.real.z,
            -c.real.x*t.real.w-c.real.w*t.real.x+c.real.z*t.real.y+c.real.y*t.real.z,
            0,0,0,0,0,0,-1,0],
            [c.real.z*t.dual.w+c.real.y*t.dual.x-c.real.x*t.dual.y-c.real.w*t.dual.z+
                c.dual.z*t.real.w+c.dual.y*t.real.x-c.dual.x*t.real.y-c.dual.w*t.real.z,
            -c.real.y*t.dual.w+c.real.z*t.dual.x-c.real.w*t.dual.y+c.real.x*t.dual.z-
                c.dual.y*t.real.w+c.dual.z*t.real.x-c.dual.w*t.real.y+c.dual.x*t.real.z,
            c.real.x*t.dual.w+c.real.w*t.dual.x+c.real.z*t.dual.y+c.real.y*t.dual.z+
                c.dual.x*t.real.w+c.dual.w*t.real.x+c.dual.z*t.real.y+c.dual.y*t.real.z,
            c.real.w*t.dual.w-c.real.x*t.dual.x-c.real.y*t.dual.y+c.real.z*t.dual.z+
                c.dual.w*t.real.w-c.dual.x*t.real.x-c.dual.y*t.real.y+c.dual.z*t.real.z,
            c.real.z*t.real.w+c.real.y*t.real.x-c.real.x*t.real.y-c.real.w*t.real.z,
            -c.real.y*t.real.w+c.real.z*t.real.x-c.real.w*t.real.y+c.real.x*t.real.z,
            c.real.x*t.real.w+c.real.w*t.real.x+c.real.z*t.real.y+c.real.y*t.real.z,
            c.real.w*t.real.w-c.real.x*t.real.x-c.real.y*t.real.y+c.real.z*t.real.z,
            0, 0, 0, 0, 0, 0, 0, -1]
            ])

    result = np.linalg.lstsq(data, np.zeros(data.shape[0]))

    G = dquat(result[0, 0], result[1, 0], result[2, 0], result[3, 0],
              result[4, 0], result[5, 0], result[6, 0], result[7, 0])
    R = dquat(result[8, 0], result[9, 0], result[10, 0], result[11, 0],
              result[12, 0], result[13, 0], result[14, 0], result[15, 0])

    print("Tool Offset: {0}".format(G))
    print("Camera to Robot: {0}".format(R))

    json_dict = {"time": str(datetime.datetime.now()),
                 "tcp2robot": G,
                 "camera2grid": R}
    with open(os.path.join(os.path.splitext(file_out)[0], '.json'), 'w') as \
            result_json_file:
        json.dump(json_dict, result_json_file, indent=4)

if __name__ == "__main__":
    main()