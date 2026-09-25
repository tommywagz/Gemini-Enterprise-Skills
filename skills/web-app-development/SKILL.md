---
name: web-app-development
description: Build or restyle web apps, websites, landing pages, and UI. Use for HTML/CSS/JS, Next.js/Vite/React scaffolding, or improving a page's design, styling, or layout.
---

# Web Application Development

## Technology Stack

Your web applications should be built using the following technologies:

1.  **Core**: Use HTML for structure and Javascript for logic.
2.  **Styling (CSS)**: Use Vanilla CSS for maximum flexibility and control.
    Avoid using TailwindCSS unless the USER explicitly requests it; in this
    case, first confirm which TailwindCSS version to use.
3.  **Web App**: If the USER specifies that they want a more complex web app,
    use a framework like Next.js or Vite. Only do this if the USER explicitly
    requests a web app.
4.  **New Project Creation**: If you need to use a framework for a new app, use
    `npx` with the appropriate script, but there are some rules to follow:
    -   Use `npx -y` to automatically install the script and its dependencies
    -   You MUST run the command with `--help` flag to see all available options
        first
    -   Initialize the app in the current directory with `./` (example:
        `npx -y create-vite-app@latest ./`)
    -   You should run in non-interactive mode so that the user doesn't need to
        input anything
5.  **Running Locally**: When running locally, use `npm run dev` or equivalent
    dev server. Only build the production bundle if the USER explicitly requests
    it or you are validating the code for correctness.

## Design Aesthetics

0.  **Function-Driven Design**: Before choosing any visual direction, analyze
    the primary utility of the product or service. Identify the most direct,
    frictionless interaction models that allow users to accomplish their goals.
    When the user does not specify particular components, layouts, or styles,
    default to the simplest, most intuitive structure for that use case. Avoid
    decorative fluff, trendy gimmicks, or unnecessary complexity.
1.  **Good design makes a product useful**: The primary job is to help users
    accomplish their goals. Be thoughtful about the information hierarchy, and
    copy should convey the appropriate information in the writing style of the
    request. Content must be easily accessible, navigation intuitive, and load
    times fast.
2.  **Prioritize Visual Excellence**: Beauty in web design is linked to utility.
    Thoughtful typography, balanced whitespace, and clear visual hierarchy make
    content a pleasure to consume.
    -   Use curated, harmonious color palettes such as HSL tailored colors.
    -   Using modern typography from Google fonts tailored to the product
        category and style, prioritizing maximum legibility, clear visual
        hierarchy, and precise typographic details (line-height, letter-spacing,
        and kerning).
3.  **Use a Dynamic Design**: An interface that feels responsive and alive
    encourages interaction. Achieve this with hover effects and interactive
    elements. Micro-animations, in particular, are highly effective for
    improving user engagement. Ensure the web page is fully responsive, in the
    simplest way possible, components and layout should adapt to the screen size
    without unnecessary content shifting. Furthermore, the internal content and
    dimensions of sub-components (such as buttons, textboxes, and input
    controls) must also be fluidly responsive to their container and screen
    size.
4.  **Premium Designs**. Make a design that feels premium and state of the art.
    Avoid creating simple minimum viable products. Nothing is arbitrary. Every
    micro-interaction, button hover state, error message, and responsive
    breakpoint is meticulously crafted and accessible.
5.  **Less, but better**. Strip away unnecessary elements until only what is
    essential remains. Every pixel must earn its place on the screen.
6.  **Forbidden Cliché Design Tropes**: UNLESS explicitly requested by the user,
    DO NOT use any of the following design patterns:
    -   **No Dashboard Overuse**: Using a dashboard design pattern for a request
        that does not require a dashboard.
    -   **No Purple on Dark**: Purple fonts or violet accents on dark theme
        backgrounds.
    -   **No Colored Border Accents**: Colored border accents or glowing colored
        outlines.
    -   **No Huge Untracked Typefaces**: Huge typefaces without proper
        letter-spacing / tracking.
    -   **No Textureless Surfaces**: Lack of texture or depth on containers and
        visual elements.
    -   **No Icon-Stuffed Bento Boxes**: Bento boxes with unrelated icons
        everywhere.
    -   **No Headline Biscuit Pills**: Biscuit/pill badge with a pulsing dot
        placed right above the main headline.
    -   **No Gradient Keywords**: CSS gradient text fills across headline
        keywords.
    -   **No Grid Backgrounds**: Grid line pattern backgrounds or particle mesh
        overlays.
    -   **No Over-Nested Cards**: Rounded cards containing three or more nested
        cards inside.
7.  **Don't use placeholders**. If you need an image, use your `generate_image`
    tool to create a working demonstration.

## Implementation Workflow

Follow this systematic approach when building web applications:

1.  **Plan and Understand**:
    -   Fully understand the user's requirements
    -   Draw inspiration from modern, beautiful, and dynamic web designs
    -   Outline the features needed for the initial version
2.  **Build the Foundation**:
    -   Start by creating/modifying `index.css`
    -   Implement the core design system with all tokens and utilities
3.  **Create Components**:
    -   Build necessary components using your design system
    -   Ensure all components use predefined styles, not ad-hoc utilities
    -   Keep components focused and reusable
4.  **Assemble Pages**:
    -   Update the main application to incorporate your design and components
    -   Ensure proper routing and navigation
    -   Implement responsive layouts
5.  **Polish and Optimize**:
    -   Review the overall user experience
    -   Ensure smooth interactions and transitions
    -   Optimize performance where needed

## SEO Best Practices

Automatically implement SEO best practices on every page:

-   **Title Tags**: Include proper, descriptive title tags for each page
-   **Meta Descriptions**: Add compelling meta descriptions that accurately
    summarize page content
-   **Heading Structure**: Use a single `<h1>` per page with proper heading
    hierarchy
-   **Semantic HTML**: Use appropriate HTML5 semantic elements
-   **Unique IDs**: Ensure all interactive elements have unique, descriptive IDs
    for browser testing
-   **Performance**: Ensure fast page load times through optimization

CRITICAL REMINDER: AESTHETICS ARE VERY IMPORTANT. If your web app looks simple
and basic then you have FAILED!
