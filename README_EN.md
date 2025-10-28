# 🚗 Automotive Tools – Blender Toolkit for Automotive Data Processing

> 🇨🇳 **中文版本请点击这里查看：** [返回中文说明文档](./README.md)  
> 📦 Current version: **v1.2** | Compatible with **Blender 4.5**

---

## 🧩 Introduction

**Automotive Tools** is a Blender add-on created for automotive industry professionals.  
It simplifies **data organization**, **structure cleanup**, and **export optimization** for car models imported from **Alias, ICEM, CATIA, NX**, and similar CAD or surface-modeling tools.

This toolkit helps make complex industrial models cleaner, lighter, and ready for visualization or game-engine export.

---

## 📥 Download & Installation

1. Download the add-on file (`.zip` or `.py`)  
2. Open **Blender → Edit → Preferences → Add-ons**  
3. Click **Install**, then choose the downloaded file  
4. Once enabled, open the **Sidebar (N)** and look for the **“AT”** tab in the 3D Viewport  

---

## ⚙️ Feature Overview

| 🧩 Feature | 💡 Description |
|-------------|----------------|
| 🧱 **Merge & Preserve Vertex Groups** | Merge multiple objects while keeping each as a separate vertex group |
| 🎯 **Select by Vertex Group Elements** | Select all elements belonging to the same vertex group |
| 🎨 **Separate by Material** | Split combined objects by material |
| 🧹 **Clean Empty Vertex Groups** | Remove unused vertex groups |
| 🌐 **Clear Custom Normal Data** | Remove custom split normals to fix shading issues |
| 📏 **Select Non-Uniform Scale** | Select objects with non-uniform or non-1.0 scale values |
| 🏷️ **Rename to Collection** | Rename objects and data by their collection name (fix long-name export errors) |
| 🔺 **Triangulate Objects** | Add triangulate modifiers to ensure correct shading after export |
| 🎭 **Select Multi-Material Objects** | Select objects with multiple material slots (user-defined threshold) |
| 🧾 **Empty to Collection (NEW in v1.2)** | Automatically create and organize collections based on object naming |
| 🧩 **Merge Duplicate Materials (NEW in v1.2)** | Automatically detect and merge duplicated materials (e.g., `Material.001 → Material`) |

---

## 🧱 Version History

### 🆕 v1.2 Additions
- 🧾 **Empty to Collection** — Automatically reorganize scene structure based on naming  
- 🧩 **Merge Duplicate Materials** — Detect and merge duplicated materials safely  

### 🧭 v1.1 Additions
- 🌐 **Clear Custom Normal Data** — Remove split normals to fix shading  
- 🎭 **Select Multi-Material Objects** — Identify models with multiple material slots  
- ⚙️ **Multi-Material Threshold Control** — User-defined minimum slot count  

### 🧰 v1.0 Core Features
- Merge vertex groups  
- Separate by material  
- Clean empty groups  
- Scale check & renaming  
- Triangulation setup  

---

## 💡 Notes & Tips

- All operations support **Undo**  
- Always **save your project** before running batch cleanup tools  
- Works well with **Datasmith** workflows  

---

## 👨‍💻 Author

**Author:** CarlMarksWX  
🔗 GitHub: [CarlMarkswx/AutomotiveTools_for_blender](https://github.com/CarlMarkswx/AutomotiveTools_for_blender/)

---

> 🇨🇳 [返回中文说明文档 / Back to Chinese README](./README.md)
