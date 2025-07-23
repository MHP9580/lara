# Logo Replacement Instructions for Congo Connect

## Current Logo Setup

The Congo Connect logo is currently set up as an SVG file that can be easily replaced with your PNG logo.

### Files to Replace:

1. **Main Logo Location**: `static/img/congo-connect-logo.svg`
   - Current: SVG placeholder logo
   - Replace with: Your PNG logo file
   - Recommended size: 200x60 pixels
   - Name your PNG file: `congo-connect-logo.png`

### How to Replace the Logo:

1. **Upload your PNG logo** to `static/img/` folder
2. **Rename your file** to `congo-connect-logo.png`
3. **Update the template** in `templates/base.html`:
   
   Replace this line (around line 26):
   ```html
   <img src="{{ url_for('static', filename='img/congo-connect-logo.svg') }}" 
   ```
   
   With:
   ```html
   <img src="{{ url_for('static', filename='img/congo-connect-logo.png') }}" 
   ```

### Where the Logo Appears:
- Navigation bar (all pages)
- Admin panel header
- Login/Registration pages
- Footer (if applicable)

### Logo Display Settings:
- Height: 40px (automatically scales width)
- Filter: White color overlay for dark navigation
- Classes: Responsive design support

### Alternative Method:
If you want to keep the current setup and just replace the SVG content:
1. Open `static/img/congo-connect-logo.svg`
2. Replace the entire SVG content with your logo design
3. Keep the same filename and dimensions