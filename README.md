The `Main` branch is a simplified version of the original repository.
It only retains two major functions as `lazy connect` and `hide socket`, as shown in the demo video below.
This is done to simplify the original add-on code from 6,000 lines, as well as to reduce the risk of shortcut conflicts with Blender functions or other add-ons, lower the learning curve, and make function management and documentation easier.

The branch `Original-Fixed-for-5.0Blender` is essentially the same as the original repository, with a single-line fix to make the add-on compatible with Blender 5.0.

Note: The add-on uses a `ctypes` hack to access socket locations for its functions. Because of this, it has been flagged as “Dangerous Malicious Code” by the original author.
Please use it at your own risk.

(In Blender add-ons, ctypes can reach parts of Blender’s memory that the normal Python API can’t.
This is powerful, but risky because:
1. Reading or writing the wrong memory can crash Blender.
2. It skips safety checks, so it may be flagged as unsafe or malicious.)


https://github.com/user-attachments/assets/388e89d0-6c04-47e4-b31f-3d9c94f3de2f

