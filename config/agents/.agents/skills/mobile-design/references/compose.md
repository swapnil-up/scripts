# Jetpack Compose Reference

## Project Setup

Android Studio → New Project → Empty Activity (Compose). Requires:
- `compileSdk 35+`
- Kotlin 2.0+
- Jetpack Compose BOM (handles version alignment)

```kotlin
// build.gradle.kts (app)
dependencies {
  val composeBom = platform("androidx.compose:compose-bom:2024.09.00")
  implementation(composeBom)
  implementation("androidx.compose.ui:ui")
  implementation("androidx.compose.material3:material3")
  implementation("androidx.compose.ui:ui-tooling-preview")
  implementation("androidx.navigation:navigation-compose:2.7.7")
  implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.4")
  debugImplementation("androidx.compose.ui:ui-tooling")
}
```

---

## Composable Architecture

Every UI element is a `@Composable` function. The key rules:

1. **Composables can only be called from composables**
2. **They must be idempotent** — the same inputs always produce the same UI
3. **No side effects in the body** — use `LaunchedEffect`, `SideEffect`, or `DisposableEffect`

```kotlin
@Composable
fun ProfileCard(
  name: String,
  avatarUrl: String,
  onClick: () -> Unit,  // ✓ event goes up, data comes down
) {
  Card(
    modifier = Modifier
      .fillMaxWidth()
      .clickable(onClick = onClick),
    shape = RoundedCornerShape(16.dp),
  ) {
    Row(
      modifier = Modifier.padding(16.dp),
      verticalAlignment = Alignment.CenterVertically,
      horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
      AsyncImage(model = avatarUrl, contentDescription = null, modifier = Modifier.size(48.dp))
      Text(name, style = MaterialTheme.typography.titleMedium)
    }
  }
}
```

---

## State Hoisting

The core pattern: **state goes up, events go down.** Don't put state inside a composable unless it's truly local (e.g., a `TextFieldValue`).

```kotlin
// ❌ State trapped inside — not reusable, not testable
@Composable
fun SearchBar() {
  var query by remember { mutableStateOf("") }
  TextField(value = query, onValueChange = { query = it })
}

// ✓ Hoisted — parent controls state, SearchBar is a pure display function
@Composable
fun SearchBar(query: String, onQueryChange: (String) -> Unit) {
  TextField(value = query, onValueChange = onQueryChange)
}

// Parent:
@Composable
fun SearchScreen(viewModel: SearchViewModel = viewModel()) {
  val query by viewModel.query.collectAsStateWithLifecycle()
  SearchBar(query = query, onQueryChange = viewModel::onQueryChange)
}
```

---

## Material 3 Theming

```kotlin
// Theme.kt
private val LightColorScheme = dynamicColorScheme(context, isDark = false)
// Or a fixed scheme:
private val LightColorScheme = lightColorScheme(
  primary = Color(0xFF6750A4),
  secondary = Color(0xFF625B71),
  // ... other tokens; M3 generates the rest
)

@Composable
fun MyAppTheme(
  darkTheme: Boolean = isSystemInDarkTheme(),
  content: @Composable () -> Unit,
) {
  val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme
  MaterialTheme(colorScheme = colorScheme, typography = AppTypography, content = content)
}

// Access tokens anywhere:
MaterialTheme.colorScheme.primary
MaterialTheme.colorScheme.surface
MaterialTheme.typography.headlineMedium
MaterialTheme.shapes.medium
```

---

## Navigation Compose

```kotlin
// NavGraph.kt
@Composable
fun AppNavHost(navController: NavHostController) {
  NavHost(navController = navController, startDestination = "home") {
    composable("home") { HomeScreen(navController) }
    composable(
      route = "detail/{itemId}",
      arguments = listOf(navArgument("itemId") { type = NavType.IntType })
    ) { backStackEntry ->
      val itemId = backStackEntry.arguments?.getInt("itemId") ?: return@composable
      DetailScreen(itemId = itemId)
    }
  }
}

// Navigate:
navController.navigate("detail/${item.id}")
navController.popBackStack()
navController.navigate("home") { popUpTo("home") { inclusive = true } }

// Bottom navigation:
NavigationBar {
  items.forEach { item ->
    NavigationBarItem(
      selected = currentRoute == item.route,
      onClick = { navController.navigate(item.route) },
      icon = { Icon(item.icon, contentDescription = item.label) },
      label = { Text(item.label) },
    )
  }
}
```

---

## Lists: LazyColumn / LazyRow

Use lazy variants for any list longer than ~15 items:

```kotlin
LazyColumn(
  verticalArrangement = Arrangement.spacedBy(12.dp),
  contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
) {
  item { HeaderSection() }
  
  items(items = data, key = { it.id }) { item ->
    ItemCard(item = item)
  }
  
  item { FooterSection() }
}

// Grid:
LazyVerticalGrid(
  columns = GridCells.Adaptive(minSize = 160.dp),
  horizontalArrangement = Arrangement.spacedBy(12.dp),
  verticalArrangement = Arrangement.spacedBy(12.dp),
) {
  items(data) { item -> GridItemCard(item) }
}
```

---

## Animations

```kotlin
// Animate a value change
val scale by animateFloatAsState(
  targetValue = if (isPressed) 0.95f else 1f,
  animationSpec = spring(dampingRatio = Spring.DampingRatioMediumBouncy),
  label = "scale",
)

Box(Modifier.graphicsLayer(scaleX = scale, scaleY = scale)) { content() }

// Animated visibility
AnimatedVisibility(
  visible = isVisible,
  enter = fadeIn() + slideInVertically(),
  exit = fadeOut() + slideOutVertically(),
) {
  content()
}

// Animate content size change
Column(Modifier.animateContentSize(animationSpec = spring())) {
  content()
  if (isExpanded) ExtraContent()
}

// Shared element transition (Compose 1.7+ / Material3 Adaptive)
// Use rememberSharedContentState + sharedElement modifier
```

---

## Haptics

```kotlin
import android.os.VibrationEffect
import android.os.Vibrator
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback

@Composable
fun HapticButton(onClick: () -> Unit) {
  val haptic = LocalHapticFeedback.current
  
  Button(onClick = {
    haptic.performHapticFeedback(HapticFeedbackType.LongPress)
    onClick()
  }) {
    Text("Press")
  }
}
```

---

## Window Insets (Safe Areas)

```kotlin
// In Scaffold (handles most cases automatically):
Scaffold(
  modifier = Modifier.fillMaxSize(),
) { innerPadding ->
  LazyColumn(
    modifier = Modifier.padding(innerPadding)
  ) { /* content */ }
}

// Fine-grained insets:
Box(
  modifier = Modifier
    .windowInsetsPadding(WindowInsets.statusBars)  // top
    .windowInsetsPadding(WindowInsets.navigationBars)  // bottom
)

// In Activity, enable edge-to-edge:
// Activity.kt:
override fun onCreate(savedInstanceState: Bundle?) {
  super.onCreate(savedInstanceState)
  enableEdgeToEdge()  // call before setContent
  setContent { MyAppTheme { AppNavHost() } }
}
```

---

## ViewModel + StateFlow Pattern

```kotlin
// ViewModel.kt
@HiltViewModel  // or just ViewModel() without Hilt
class HomeViewModel @Inject constructor(
  private val repository: ItemRepository
) : ViewModel() {

  private val _uiState = MutableStateFlow(HomeUiState())
  val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()

  init { loadItems() }

  fun loadItems() {
    viewModelScope.launch {
      _uiState.update { it.copy(isLoading = true) }
      val result = repository.getItems()
      _uiState.update { it.copy(items = result, isLoading = false) }
    }
  }
}

data class HomeUiState(
  val items: List<Item> = emptyList(),
  val isLoading: Boolean = false,
  val error: String? = null,
)

// Composable:
@Composable
fun HomeScreen(viewModel: HomeViewModel = viewModel()) {
  val uiState by viewModel.uiState.collectAsStateWithLifecycle()
  
  when {
    uiState.isLoading -> LoadingScreen()
    uiState.error != null -> ErrorScreen(uiState.error!!)
    else -> ItemList(uiState.items)
  }
}
```

---

## Common Gotchas

- `Modifier` order matters — `Modifier.padding(16.dp).background(color)` ≠ `Modifier.background(color).padding(16.dp)`
- `remember` survives recomposition but NOT navigation or configuration changes — use `rememberSaveable` or ViewModel for that
- `LazyColumn` inside a `Column` causes an infinite height error — use `weight(1f)` on the `LazyColumn` or replace the `Column` with a `Scaffold`
- `clickable` on a composable with no ripple still needs `indication = null, interactionSource = null` to suppress the ripple
- `by` delegate (`val x by remember { ... }`) requires `getValue`/`setValue` operators — import `androidx.compose.runtime.getValue` / `setValue`
- Dark mode: `isSystemInDarkTheme()` is the right way to check; don't read `Configuration` directly
- `String` resources should be loaded with `stringResource(R.string.key)` — don't hardcode strings directly in composables for production apps