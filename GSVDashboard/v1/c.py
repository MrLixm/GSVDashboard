"""
Constants

[LICENSE]

    Copyright 2022 Liam Collod
    
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
    
       http://www.apache.org/licenses/LICENSE-2.0
    
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

"""

name = "GSVDashboard"

v_major = 2
v_minor = 1  # have to update the Node if incremented
v_patch = 0  # bug fix not affecting the Node structure

v_dev = 19
v_published = 108  # auto incremented when tested

# used to determine if the Node need to be updated
version = int("{}{}".format(v_major, v_minor))