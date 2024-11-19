import { withShurikenUI } from '@shuriken-ui/tailwind'
import colors from 'tailwindcss/colors'

/**
 * The `withShurikenUI` function injects the Shuriken UI preset 
 * into the Tailwind CSS configuration,
 * 
 * Allows VSCode to provide autocompletion 
 * for Tailwind CSS classes.
 */
export default withShurikenUI({
  /**
   * The content property is automatically populated 
   * to include all nuxt files, but you can add 
   * additional files so that Tailwind CSS can 
   * extract the classes from them.
   */
  darkMode: 'class',
  content: [],
  /**
   * You can add additional plugins to Tailwind CSS 
   * by adding them to the plugins list here.
   */
  plugins: [
    // Your custom plugins goes here
    "@tailwindcss/typography"
  ],
  /**
   * Define your custom Tailwind CSS theme here
   */
  theme: {
    extend: {
      // Your custom theme properties goes here
    },
  },
})
